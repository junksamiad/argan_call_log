import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { initialQuery } = await request.json()

    console.log("API: Received request with initialQuery:", initialQuery)

    if (!initialQuery) {
      return NextResponse.json({ error: "No initial query provided" }, { status: 400 })
    }

    const apiKey = process.env.OPENAI_API_KEY

    if (!apiKey) {
      console.error("API: OpenAI API key not found in environment variables")
      return NextResponse.json({ error: "OpenAI API key not configured" }, { status: 500 })
    }

    console.log("API: OpenAI API key found, length:", apiKey.length)

    // Parse the initial query if it's a string
    let queryData
    try {
      queryData = typeof initialQuery === "string" ? JSON.parse(initialQuery) : initialQuery
      console.log("API: Parsed query data:", queryData)
    } catch (err) {
      console.log("API: Failed to parse as JSON, using as string")
      queryData = { content: initialQuery }
    }

    // Extract the main content for HR solution generation
    const clientQuery =
      queryData.sender_content ||
      queryData.email_content ||
      queryData.content ||
      queryData.sender_email_content ||
      JSON.stringify(queryData)

    const clientName = queryData.sender_name || queryData.name || "the client"
    const careHomeName = queryData.care_home_name || "the care home"

    console.log("API: Client query to analyze:", clientQuery)

    const requestBody = {
      model: "gpt-4.1",
      messages: [
        {
          role: "system",
          content: `You are a professional HR consultant at Argan Consultancy, specializing in care home HR issues. You provide expert, practical, and legally compliant HR advice to care home operators across the UK.

Your responses should be:
- Professional and authoritative
- Practical and actionable
- Legally compliant with UK employment law
- Specific to the care home sector
- Well-structured and easy to follow
- Include relevant policies, procedures, or documentation where appropriate

Format your response in clear markdown with appropriate headings, bullet points, and emphasis where needed.`,
        },
        {
          role: "user",
          content: `I have received the following HR query from ${clientName} at ${careHomeName}:

"${clientQuery}"

Please provide a comprehensive, professional HR solution that addresses this issue. Include:

1. **Immediate Actions** - What should be done right away
2. **Investigation Process** - If applicable, how to properly investigate
3. **Policy Considerations** - Relevant policies that should be reviewed or implemented
4. **Legal Compliance** - Key legal considerations and requirements
5. **Documentation** - What should be documented and how
6. **Next Steps** - Clear action plan moving forward
7. **Prevention** - How to prevent similar issues in the future

Please ensure the advice is specific to the care home sector and compliant with current UK employment legislation.`,
        },
      ],
      temperature: 0.7,
      max_tokens: 2000,
    }

    console.log("API: Making request to OpenAI")

    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(requestBody),
    })

    console.log("API: OpenAI response status:", response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error("API: OpenAI API error:", errorText)
      return NextResponse.json(
        { error: `OpenAI API error: ${response.status} - ${errorText}` },
        { status: response.status },
      )
    }

    const data = await response.json()
    console.log("API: OpenAI response data:", data)

    // Extract the HR solution from the response
    let hrSolution = "Unable to generate HR solution"

    if (data.choices && data.choices.length > 0 && data.choices[0].message) {
      hrSolution = data.choices[0].message.content
    }

    console.log("API: Extracted HR solution:", hrSolution)

    return NextResponse.json({ hrSolution })
  } catch (error) {
    console.error("API: Error generating HR solution:", error)
    return NextResponse.json(
      {
        error: `Failed to generate HR solution: ${error instanceof Error ? error.message : "Unknown error"}`,
      },
      { status: 500 },
    )
  }
}
