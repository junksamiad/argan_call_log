import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { ticketNumber, newStatus } = await request.json()

    if (!ticketNumber || !newStatus) {
      return NextResponse.json({ error: "Ticket number and new status are required" }, { status: 400 })
    }

    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID
    const tableName = process.env.AIRTABLE_TABLE_NAME

    if (!apiKey || !baseId || !tableName) {
      return NextResponse.json({ error: "Airtable configuration missing" }, { status: 500 })
    }

    // First, find the record with the matching ticket number
    const searchUrl = `https://api.airtable.com/v0/${baseId}/${encodeURIComponent(tableName)}?filterByFormula={ticket_number}="${ticketNumber}"`

    const searchResponse = await fetch(searchUrl, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
    })

    if (!searchResponse.ok) {
      const errorText = await searchResponse.text()
      console.error("Airtable search error:", errorText)
      throw new Error(`Failed to find ticket: ${searchResponse.status}`)
    }

    const searchData = await searchResponse.json()

    if (!searchData.records || searchData.records.length === 0) {
      return NextResponse.json({ error: "Ticket not found" }, { status: 404 })
    }

    const recordId = searchData.records[0].id

    // Update the record with the new status
    const updateUrl = `https://api.airtable.com/v0/${baseId}/${encodeURIComponent(tableName)}/${recordId}`

    const updatePayload = {
      fields: {
        status: newStatus,
      },
    }

    console.log("Updating record status:", { recordId, ticketNumber, newStatus })

    const updateResponse = await fetch(updateUrl, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(updatePayload),
    })

    if (!updateResponse.ok) {
      const errorText = await updateResponse.text()
      console.error("Airtable update error:", errorText)
      throw new Error(`Failed to update record: ${updateResponse.status} - ${errorText}`)
    }

    const updateData = await updateResponse.json()

    return NextResponse.json({
      success: true,
      message: "Status updated successfully",
      recordId: updateData.id,
      newStatus,
    })
  } catch (error) {
    console.error("Error updating status:", error)
    return NextResponse.json(
      { error: `Failed to update status: ${error instanceof Error ? error.message : "Unknown error"}` },
      { status: 500 },
    )
  }
}

export async function GET() {
  try {
    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID
    const tableName = process.env.AIRTABLE_TABLE_NAME

    if (!apiKey || !baseId || !tableName) {
      return NextResponse.json({ error: "Airtable configuration missing" }, { status: 500 })
    }

    // Get the table schema to extract field options
    const schemaUrl = `https://api.airtable.com/v0/meta/bases/${baseId}/tables`

    const schemaResponse = await fetch(schemaUrl, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
    })

    if (!schemaResponse.ok) {
      const errorText = await schemaResponse.text()
      console.error("Airtable schema API error:", errorText)
      throw new Error(`Failed to fetch table schema: ${schemaResponse.status}`)
    }

    const schemaData = await schemaResponse.json()

    // Find the table and the status field
    const table = schemaData.tables?.find((t: any) => t.name === tableName)
    if (!table) {
      throw new Error(`Table ${tableName} not found`)
    }

    const statusField = table.fields?.find((f: any) => f.name === "status")
    if (!statusField) {
      throw new Error("Status field not found")
    }

    // Extract the options from the single select field with their colors
    const statusOptions =
      statusField.options?.choices?.map((choice: any) => ({
        name: choice.name,
        color: choice.color,
      })) || []

    console.log("Found status field options with colors:", statusOptions)

    // If we can't get the colors from the schema, use our predefined colors
    const statusesWithColors =
      statusOptions.length > 0
        ? statusOptions
        : [
            { name: "open - awaiting client response", color: "yellow" },
            { name: "open - awaiting argan response", color: "red" },
            { name: "resolved", color: "green" },
          ]

    return NextResponse.json({
      success: true,
      statusOptions: statusesWithColors,
    })
  } catch (error) {
    console.error("Error fetching status field options:", error)

    // Fallback: if schema API fails, return predefined status values with colors
    const fallbackStatuses = [
      { name: "open - awaiting client response", color: "yellow" },
      { name: "open - awaiting argan response", color: "red" },
      { name: "resolved", color: "green" },
    ]

    return NextResponse.json({
      success: true,
      statusOptions: fallbackStatuses,
      fallback: true,
    })
  }
}
