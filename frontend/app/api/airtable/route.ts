import { NextResponse } from "next/server"

export async function GET() {
  try {
    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID
    const tableName = process.env.AIRTABLE_TABLE_NAME

    console.log("Environment variables:", {
      apiKey: apiKey ? "Set" : "Not set",
      baseId: baseId ? "Set" : "Not set",
      tableName: tableName ? "Set" : "Not set",
    })

    console.log("Full environment check:", {
      NODE_ENV: process.env.NODE_ENV,
      allEnvKeys: Object.keys(process.env).filter((key) => key.includes("AIRTABLE")),
      apiKeyLength: apiKey?.length || 0,
      baseIdLength: baseId?.length || 0,
      tableNameLength: tableName?.length || 0,
    })

    if (!apiKey || !baseId || !tableName) {
      return NextResponse.json(
        {
          error: "Missing Airtable configuration",
          details: {
            apiKey: !apiKey ? "Missing" : "Present",
            baseId: !baseId ? "Missing" : "Present",
            tableName: !tableName ? "Missing" : "Present",
          },
        },
        { status: 500 },
      )
    }

    const url = `https://api.airtable.com/v0/${baseId}/${encodeURIComponent(tableName)}`
    console.log("Fetching from URL:", url)

    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      cache: "no-store",
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Airtable API error:", errorText)
      return NextResponse.json(
        {
          error: `Airtable API error: ${response.status}`,
          details: errorText,
        },
        { status: response.status },
      )
    }

    const data = await response.json()
    console.log("Successfully fetched data:", data.records?.length || 0, "records")

    // Log the first record to see its structure
    if (data.records && data.records.length > 0) {
      console.log("First record:", {
        id: data.records[0].id,
        fields: Object.keys(data.records[0].fields),
        fieldValues: data.records[0].fields,
      })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error("Error fetching from Airtable:", error)
    return NextResponse.json(
      {
        error: "Failed to fetch data from Airtable",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}
