import { NextResponse } from "next/server"

export async function POST(request: Request) {
  try {
    const { ticketNumber, aiQueryResponse } = await request.json()

    if (!ticketNumber || !aiQueryResponse) {
      return NextResponse.json({ error: "Ticket number and AI response are required" }, { status: 400 })
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

    // Update the record with the AI query response
    const updateUrl = `https://api.airtable.com/v0/${baseId}/${encodeURIComponent(tableName)}/${recordId}`

    const updatePayload = {
      fields: {
        ai_query_response: aiQueryResponse,
      },
    }

    console.log("Updating record with AI response:", { recordId, ticketNumber })

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
      message: "AI query response saved successfully",
      recordId: updateData.id,
    })
  } catch (error) {
    console.error("Error saving AI query response:", error)
    return NextResponse.json(
      { error: `Failed to save AI query response: ${error instanceof Error ? error.message : "Unknown error"}` },
      { status: 500 },
    )
  }
}
