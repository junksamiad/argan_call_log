import { NextResponse } from "next/server"

export async function GET() {
  try {
    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID
    const tableName = process.env.AIRTABLE_TABLE_NAME

    if (!apiKey || !baseId || !tableName) {
      return NextResponse.json({ error: "Airtable configuration missing" }, { status: 500 })
    }

    // Fetch records that have an ai_summary field
    const url = `https://api.airtable.com/v0/${baseId}/${encodeURIComponent(tableName)}?filterByFormula=NOT({ai_summary}='')`

    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Airtable API error:", errorText)
      throw new Error(`Failed to fetch records: ${response.status}`)
    }

    const data = await response.json()

    // Extract the relevant fields for the report
    const reportData = data.records.map((record: any) => ({
      id: record.id,
      ticketNumber: record.fields.ticket_number || "N/A",
      careHomeName: record.fields.care_home_name || "Unknown Care Home",
      subject: record.fields.subject || "No Subject",
      status: record.fields.status || "unknown",
      createdDate: record.fields.created_at || record.createdTime,
      aiSummary: record.fields.ai_summary || "",
    }))

    return NextResponse.json({
      success: true,
      reportData,
    })
  } catch (error) {
    console.error("Error generating report data:", error)
    return NextResponse.json(
      { error: `Failed to generate report data: ${error instanceof Error ? error.message : "Unknown error"}` },
      { status: 500 },
    )
  }
}
