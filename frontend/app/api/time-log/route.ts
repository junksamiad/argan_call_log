import { NextResponse } from "next/server"

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const ticketNumber = searchParams.get("ticketNumber")
    const fetchEntries = searchParams.get("fetchEntries") === "true"

    if (!ticketNumber) {
      return NextResponse.json({ error: "Ticket number is required" }, { status: 400 })
    }

    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID

    if (!apiKey || !baseId) {
      return NextResponse.json({ error: "Airtable configuration missing" }, { status: 500 })
    }

    // First, get the record ID from the main table for this ticket number
    const mainTableUrl = `https://api.airtable.com/v0/${baseId}/argan_call_log?filterByFormula={ticket_number}="${ticketNumber}"`

    const mainTableResponse = await fetch(mainTableUrl, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
    })

    if (!mainTableResponse.ok) {
      throw new Error(`Failed to fetch main table record: ${mainTableResponse.status}`)
    }

    const mainTableData = await mainTableResponse.json()

    if (!mainTableData.records || mainTableData.records.length === 0) {
      return NextResponse.json({ error: "Ticket not found" }, { status: 404 })
    }

    const mainRecordId = mainTableData.records[0].id

    // Get staff records to map names to IDs
    const staffUrl = `https://api.airtable.com/v0/${baseId}/staff`
    const staffResponse = await fetch(staffUrl, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
    })

    let staffRecords = []
    let staffMap = {}
    if (staffResponse.ok) {
      const staffData = await staffResponse.json()
      staffRecords = staffData.records || []

      // Create a map of staff IDs to names for easier lookup
      staffMap = staffRecords.reduce((acc, staff) => {
        acc[staff.id] = staff.fields.name || staff.fields.staff_name || "Unknown"
        return acc
      }, {})
    }

    // Now get existing time log entries for this ticket
    // Use a simpler filter formula to ensure we get all entries
    const timeLogUrl = `https://api.airtable.com/v0/${baseId}/time_log`

    const timeLogResponse = await fetch(timeLogUrl, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
    })

    if (!timeLogResponse.ok) {
      throw new Error(`Failed to fetch time log entries: ${timeLogResponse.status}`)
    }

    const timeLogData = await timeLogResponse.json()

    // Filter entries manually to ensure we get all entries for this ticket
    const allEntries = timeLogData.records || []
    console.log(`Found ${allEntries.length} total time log entries`)

    // Filter entries that belong to this ticket
    const ticketEntries = allEntries.filter((entry) => {
      if (!entry.fields.ticket || !Array.isArray(entry.fields.ticket)) return false
      return entry.fields.ticket.includes(mainRecordId)
    })

    console.log(`Found ${ticketEntries.length} time log entries for ticket ${ticketNumber}`)

    // Calculate the next entry number
    const maxEntryNumber = ticketEntries.reduce((max, record) => {
      const entryNumber = Number.parseInt(record.fields.time_log_entry) || 0
      return Math.max(max, entryNumber)
    }, 0)

    const nextEntryNumber = maxEntryNumber + 1

    // Process time log entries if requested
    let timeLogEntries = []
    let totalTimeLogged = 0

    if (fetchEntries) {
      timeLogEntries = ticketEntries
        .map((entry) => {
          // Get assignee name from the staff map
          let assigneeName = "Unknown"
          if (entry.fields.assignee && entry.fields.assignee.length > 0) {
            assigneeName = staffMap[entry.fields.assignee[0]] || "Unknown"
          }

          // Calculate time in hours and minutes
          const timeInSeconds = entry.fields.time_logged || 0
          const hours = Math.floor(timeInSeconds / 3600)
          const minutes = Math.floor((timeInSeconds % 3600) / 60)

          // Add to total
          totalTimeLogged += timeInSeconds

          return {
            id: entry.id,
            entryNumber: entry.fields.time_log_entry,
            assignee: assigneeName,
            description: entry.fields.description_of_task || "",
            timeLogged: timeInSeconds,
            formattedTime: `${hours}h ${minutes}m`,
            createdTime: entry.createdTime,
          }
        })
        .sort((a, b) => {
          // Sort by entry number
          return Number.parseInt(a.entryNumber) - Number.parseInt(b.entryNumber)
        })
    }

    // Calculate total time in hours and minutes
    const totalHours = Math.floor(totalTimeLogged / 3600)
    const totalMinutes = Math.floor((totalTimeLogged % 3600) / 60)

    return NextResponse.json({
      nextEntryNumber,
      mainRecordId,
      existingEntries: ticketEntries.length,
      staffRecords: staffRecords.map((record) => ({
        id: record.id,
        name: record.fields.name || record.fields.staff_name || "Unknown",
      })),
      timeLogEntries,
      totalTimeLogged,
      formattedTotalTime: `${totalHours}h ${totalMinutes}m`,
    })
  } catch (error) {
    console.error("Error fetching time log data:", error)
    return NextResponse.json(
      { error: `Failed to fetch time log data: ${error instanceof Error ? error.message : "Unknown error"}` },
      { status: 500 },
    )
  }
}

export async function POST(request: Request) {
  try {
    const { ticketNumber, assigneeId, description, timeLogged, mainRecordId, entryNumber } = await request.json()

    if (!ticketNumber || !assigneeId || !description || !timeLogged || !mainRecordId || !entryNumber) {
      return NextResponse.json({ error: "All fields are required" }, { status: 400 })
    }

    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID

    if (!apiKey || !baseId) {
      return NextResponse.json({ error: "Airtable configuration missing" }, { status: 500 })
    }

    // Create the time log entry
    const url = `https://api.airtable.com/v0/${baseId}/time_log`

    const payload = {
      fields: {
        time_log_entry: String(entryNumber),
        assignee: [assigneeId], // Array of record IDs from staff table
        description_of_task: description,
        time_logged: Number(timeLogged),
        ticket: [mainRecordId], // Array of record IDs from main table
      },
    }

    console.log("Sending payload to Airtable:", JSON.stringify(payload, null, 2))

    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Airtable API error:", errorText)
      throw new Error(`Failed to create time log entry: ${response.status} - ${errorText}`)
    }

    const data = await response.json()

    return NextResponse.json({
      success: true,
      record: data,
      message: `Time log entry #${entryNumber} created successfully`,
    })
  } catch (error) {
    console.error("Error creating time log entry:", error)
    return NextResponse.json(
      { error: `Failed to create time log entry: ${error instanceof Error ? error.message : "Unknown error"}` },
      { status: 500 },
    )
  }
}
