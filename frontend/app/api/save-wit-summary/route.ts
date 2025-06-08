import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { ticketNumber, witSummary } = await request.json()

    if (!ticketNumber || !witSummary) {
      return NextResponse.json({ error: "Ticket number and WiT summary are required" }, { status: 400 })
    }

    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID
    const tableName = process.env.AIRTABLE_TABLE_NAME

    if (!apiKey || !baseId || !tableName) {
      return NextResponse.json({ error: "Airtable configuration missing" }, { status: 500 })
    }

    const searchUrl = `https://api.airtable.com/v0/${baseId}/${encodeURIComponent(tableName)}?filterByFormula={ticket_number}="${ticketNumber}"`
    const searchResponse = await fetch(searchUrl, {
      headers: { Authorization: `Bearer ${apiKey}` },
    })

    if (!searchResponse.ok) throw new Error(`Failed to find ticket: ${searchResponse.status}`)
    const searchData = await searchResponse.json()
    if (!searchData.records || searchData.records.length === 0) {
      return NextResponse.json({ error: "Ticket not found" }, { status: 404 })
    }

    const recordId = searchData.records[0].id
    const updateUrl = `https://api.airtable.com/v0/${baseId}/${encodeURIComponent(tableName)}/${recordId}`
    const updatePayload = { fields: { wit_summary: witSummary } } // Assuming new field name 'wit_summary'

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
      throw new Error(`Failed to update record: ${updateResponse.status} - ${errorText}`)
    }

    return NextResponse.json({ success: true, message: "WiT summary saved successfully" })
  } catch (error) {
    console.error("Error saving WiT summary:", error)
    return NextResponse.json(
      { error: `Failed to save WiT summary: ${error instanceof Error ? error.message : "Unknown error"}` },
      { status: 500 },
    )
  }
}
