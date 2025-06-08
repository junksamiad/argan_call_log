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

    // Search for the record with the matching ticket number
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

    const record = searchData.records[0]
    const existingSummary = record.fields.ai_summary

    return NextResponse.json({
      hasExistingSummary: !!existingSummary,
      existingSummary: existingSummary || null,
      recordId: record.id,
    })
  } catch (error) {
    console.error("Error checking AI summary:", error)
    return NextResponse.json(
      { error: `Failed to check AI summary: ${error instanceof Error ? error.message : "Unknown error"}` },
      { status: 500 },
    )
  }
}
