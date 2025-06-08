import { NextResponse } from "next/server"

export async function GET() {
  try {
    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID

    if (!apiKey || !baseId) {
      return NextResponse.json({ error: "Missing Airtable configuration" }, { status: 500 })
    }

    const url = `https://api.airtable.com/v0/${baseId}/staff`

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
      return NextResponse.json({ error: `Airtable API error: ${response.status}` }, { status: response.status })
    }

    const data = await response.json()

    // Transform the data to a simpler format
    const staffMembers = data.records.map((record: any) => ({
      id: record.id,
      name: record.fields.name || record.fields.staff_name || "Unnamed Staff",
    }))

    return NextResponse.json({ staffMembers })
  } catch (error) {
    console.error("Error fetching staff members:", error)
    return NextResponse.json({ error: "Failed to fetch staff members" }, { status: 500 })
  }
}

export async function POST(request: Request) {
  try {
    const { name } = await request.json()

    if (!name || typeof name !== "string" || !name.trim()) {
      return NextResponse.json({ error: "Staff name is required" }, { status: 400 })
    }

    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID

    if (!apiKey || !baseId) {
      return NextResponse.json({ error: "Missing Airtable configuration" }, { status: 500 })
    }

    const url = `https://api.airtable.com/v0/${baseId}/staff`

    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        fields: {
          name: name.trim(),
        },
      }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Airtable API error:", errorText)
      return NextResponse.json({ error: `Airtable API error: ${response.status}` }, { status: response.status })
    }

    const data = await response.json()

    return NextResponse.json({
      success: true,
      staffMember: {
        id: data.id,
        name: data.fields.name,
      },
    })
  } catch (error) {
    console.error("Error creating staff member:", error)
    return NextResponse.json({ error: "Failed to create staff member" }, { status: 500 })
  }
}
