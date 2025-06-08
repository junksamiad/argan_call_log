import { NextResponse } from "next/server"

export async function PUT(request: Request, { params }: { params: { id: string } }) {
  try {
    const { id } = params
    const { name } = await request.json()

    if (!name || typeof name !== "string" || !name.trim()) {
      return NextResponse.json({ error: "Staff name is required" }, { status: 400 })
    }

    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID

    if (!apiKey || !baseId) {
      return NextResponse.json({ error: "Missing Airtable configuration" }, { status: 500 })
    }

    const url = `https://api.airtable.com/v0/${baseId}/staff/${id}`

    const response = await fetch(url, {
      method: "PATCH",
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
    console.error("Error updating staff member:", error)
    return NextResponse.json({ error: "Failed to update staff member" }, { status: 500 })
  }
}

export async function DELETE(request: Request, { params }: { params: { id: string } }) {
  try {
    const { id } = params

    const apiKey = process.env.AIRTABLE_API_KEY
    const baseId = process.env.AIRTABLE_BASE_ID

    if (!apiKey || !baseId) {
      return NextResponse.json({ error: "Missing Airtable configuration" }, { status: 500 })
    }

    const url = `https://api.airtable.com/v0/${baseId}/staff/${id}`

    const response = await fetch(url, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error("Airtable API error:", errorText)
      return NextResponse.json({ error: `Airtable API error: ${response.status}` }, { status: response.status })
    }

    return NextResponse.json({
      success: true,
      message: "Staff member deleted successfully",
    })
  } catch (error) {
    console.error("Error deleting staff member:", error)
    return NextResponse.json({ error: "Failed to delete staff member" }, { status: 500 })
  }
}
