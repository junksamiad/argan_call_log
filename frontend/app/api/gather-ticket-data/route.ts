import { NextResponse } from "next/server"

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const ticketNumber = searchParams.get("ticketNumber")

    if (!ticketNumber) {
      return NextResponse.json({ error: "Ticket number is required" }, { status: 400 })
    }

    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID
    const tableName = process.env.AIRTABLE_TABLE_NAME

    if (!apiKey || !baseId || !tableName) {
      return NextResponse.json({ error: "Airtable configuration missing" }, { status: 500 })
    }

    // Get the main ticket record
    const mainTableUrl = `https://api.airtable.com/v0/${baseId}/${encodeURIComponent(tableName)}?filterByFormula={ticket_number}="${ticketNumber}"`

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

    const mainRecord = mainTableData.records[0]
    const mainRecordId = mainRecord.id

    // Get staff records for name mapping
    const staffUrl = `https://api.airtable.com/v0/${baseId}/staff`
    const staffResponse = await fetch(staffUrl, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
    })

    let staffMap = {}
    if (staffResponse.ok) {
      const staffData = await staffResponse.json()
      const staffRecords = staffData.records || []
      staffMap = staffRecords.reduce((acc, staff) => {
        acc[staff.id] = staff.fields.name || staff.fields.staff_name || "Unknown"
        return acc
      }, {})
    }

    // Get time log entries for this ticket
    const timeLogUrl = `https://api.airtable.com/v0/${baseId}/time_log`
    const timeLogResponse = await fetch(timeLogUrl, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
    })

    let timeLogEntries = []
    let totalTimeLogged = 0

    if (timeLogResponse.ok) {
      const timeLogData = await timeLogResponse.json()
      const allEntries = timeLogData.records || []

      // Filter entries that belong to this ticket
      const ticketEntries = allEntries.filter((entry) => {
        if (!entry.fields.ticket || !Array.isArray(entry.fields.ticket)) return false
        return entry.fields.ticket.includes(mainRecordId)
      })

      timeLogEntries = ticketEntries
        .map((entry) => {
          const timeInSeconds = entry.fields.time_logged || 0
          totalTimeLogged += timeInSeconds

          let assigneeName = "Unknown"
          if (entry.fields.assignee && entry.fields.assignee.length > 0) {
            assigneeName = staffMap[entry.fields.assignee[0]] || "Unknown"
          }

          return {
            id: entry.id,
            entryNumber: entry.fields.time_log_entry,
            assignee: assigneeName,
            description: entry.fields.description_of_task || "",
            timeLogged: timeInSeconds,
            createdTime: entry.createdTime,
          }
        })
        .sort((a, b) => Number.parseInt(a.entryNumber) - Number.parseInt(b.entryNumber))
    }

    // Parse conversation history
    let conversationHistory = []
    try {
      if (mainRecord.fields.conversation_history) {
        const historyData =
          typeof mainRecord.fields.conversation_history === "string"
            ? JSON.parse(mainRecord.fields.conversation_history)
            : mainRecord.fields.conversation_history

        if (Array.isArray(historyData)) {
          conversationHistory = historyData.sort((a, b) => {
            if (a.chronological_order !== undefined && b.chronological_order !== undefined) {
              return a.chronological_order - b.chronological_order
            }

            // Use safer string comparison for dates that might not parse correctly
            const dateA = a.sender_email_date || a.timestamp || ""
            const dateB = b.sender_email_date || b.timestamp || ""
            return dateA.localeCompare(dateB)
          })
        }
      }
    } catch (err) {
      console.error("Error parsing conversation history:", err)
    }

    // Parse initial conversation query
    let initialQuery = null
    try {
      if (mainRecord.fields.initial_conversation_query) {
        initialQuery =
          typeof mainRecord.fields.initial_conversation_query === "string"
            ? JSON.parse(mainRecord.fields.initial_conversation_query)
            : mainRecord.fields.initial_conversation_query
      }
    } catch (err) {
      console.error("Error parsing initial query:", err)
    }

    // Helper function to safely parse dates in various formats
    function safeParseDate(dateStr) {
      if (!dateStr) return null

      try {
        // Try direct parsing first
        const date = new Date(dateStr)
        if (!isNaN(date.getTime())) return date

        // Try parsing UK format DD/MM/YYYY
        if (dateStr.includes("/")) {
          const parts = dateStr.split(" ")[0].split("/")
          if (parts.length === 3) {
            // UK format DD/MM/YYYY
            const day = Number.parseInt(parts[0], 10)
            const month = Number.parseInt(parts[1], 10) - 1 // Months are 0-indexed in JS
            const year = Number.parseInt(parts[2], 10)

            // Extract time if available
            let hours = 0,
              minutes = 0
            if (dateStr.includes(":")) {
              const timeParts = dateStr.split(" ")[1].split(":")
              hours = Number.parseInt(timeParts[0], 10)
              minutes = Number.parseInt(timeParts[1], 10)
            }

            const date = new Date(year, month, day, hours, minutes)
            if (!isNaN(date.getTime())) return date
          }
        }

        return null
      } catch (e) {
        console.error("Error parsing date:", dateStr, e)
        return null
      }
    }

    // Calculate response times
    const ticketCreatedDate = safeParseDate(mainRecord.fields.created_at || mainRecord.createdTime)
    let firstArganResponse = null
    let responseTimeHours = null

    // Find first Argan response
    for (const conv of conversationHistory) {
      if (conv.sender_email && conv.sender_email.includes("@arganhrconsultancy.co.uk")) {
        firstArganResponse = safeParseDate(conv.sender_email_date || conv.timestamp)
        if (firstArganResponse && ticketCreatedDate) {
          responseTimeHours = (firstArganResponse.getTime() - ticketCreatedDate.getTime()) / (1000 * 60 * 60)
        }
        break
      }
    }

    // Prepare comprehensive data for AI
    const ticketData = {
      ticketInfo: {
        ticketNumber: mainRecord.fields.ticket_number,
        careHomeName: mainRecord.fields.care_home_name,
        subject: mainRecord.fields.subject,
        status: mainRecord.fields.status,
        createdDate: mainRecord.fields.created_at || mainRecord.createdTime,
      },
      initialQuery,
      conversationHistory,
      timeLogEntries,
      timeLogSummary: {
        totalEntries: timeLogEntries.length,
        totalTimeLogged,
        totalTimeFormatted: `${Math.floor(totalTimeLogged / 3600)}h ${Math.floor((totalTimeLogged % 3600) / 60)}m`,
      },
      responseTimes: {
        firstArganResponse: firstArganResponse ? firstArganResponse.toISOString() : null,
        responseTimeHours,
        responseTimeFormatted: responseTimeHours
          ? `${Math.round(responseTimeHours * 10) / 10} hours`
          : "No response yet",
      },
      arganStaffInvolved: [
        ...new Set(
          conversationHistory
            .filter((conv) => conv.sender_email && conv.sender_email.includes("@arganhrconsultancy.co.uk"))
            .map((conv) => conv.sender_name || conv.sender_email),
        ),
      ],
    }

    return NextResponse.json({
      success: true,
      ticketData,
    })
  } catch (error) {
    console.error("Error gathering ticket data:", error)
    return NextResponse.json(
      { error: `Failed to gather ticket data: ${error instanceof Error ? error.message : "Unknown error"}` },
      { status: 500 },
    )
  }
}
