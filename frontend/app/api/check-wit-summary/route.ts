import { NextResponse } from "next/server"

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const ticketNumber = searchParams.get("ticketNumber")

    if (!ticketNumber) {
      console.log("Check WiT Summary API: Ticket number is required")
      return NextResponse.json({ error: "Ticket number is required" }, { status: 400 })
    }

    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID
    const tableName = process.env.AIRTABLE_TABLE_NAME

    if (!apiKey || !baseId || !tableName) {
      console.error("Check WiT Summary API: Airtable configuration missing")
      return NextResponse.json({ error: "Airtable configuration missing" }, { status: 500 })
    }

    // Fetch the record by ticket_number. Do not specify fields[] initially to be more robust.
    // If the record is found, we'll check for the wit_summary field in its data.
    const searchUrl = `https://api.airtable.com/v0/${baseId}/${encodeURIComponent(tableName)}?filterByFormula={ticket_number}="${ticketNumber}"`

    console.log(`Check WiT Summary API: Fetching from Airtable URL: ${searchUrl}`)

    const searchResponse = await fetch(searchUrl, {
      headers: { Authorization: `Bearer ${apiKey}` },
    })

    if (!searchResponse.ok) {
      const errorText = await searchResponse.text()
      console.error(
        `Check WiT Summary API: Airtable API error (${searchResponse.status}). URL: ${searchUrl}. Details: ${errorText}`,
      )
      // Provide more context from Airtable if available
      throw new Error(`Failed to find ticket: ${searchResponse.status}. Details: ${errorText}`)
    }

    const searchData = await searchResponse.json()

    if (!searchData.records || searchData.records.length === 0) {
      console.log(`Check WiT Summary API: Ticket ${ticketNumber} not found.`)
      return NextResponse.json({ error: "Ticket not found" }, { status: 404 })
    }

    const record = searchData.records[0]
    // Check for the 'wit_summary' field in the retrieved record.
    // This assumes the field name in Airtable is 'wit_summary'.
    const existingSummary = record.fields.wit_summary

    console.log(
      `Check WiT Summary API: Ticket ${ticketNumber} found. WiT summary exists: ${!!existingSummary}. Summary (first 50 chars): ${existingSummary ? String(existingSummary).substring(0, 50) : "N/A"}`,
    )

    return NextResponse.json({
      hasExistingSummary: !!existingSummary,
      existingSummary: existingSummary || null,
      // recordId: record.id // Optionally return recordId if needed elsewhere
    })
  } catch (error) {
    console.error("Check WiT Summary API: Error checking WiT summary:", error)
    return NextResponse.json(
      { error: `Failed to check WiT summary: ${error instanceof Error ? error.message : "Unknown error"}` },
      { status: 500 },
    )
  }
}
