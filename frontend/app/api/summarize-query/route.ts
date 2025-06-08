import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { conversationQuery } = await request.json()

    console.log("API: Received request with conversationQuery:", conversationQuery)

    if (!conversationQuery) {
      return NextResponse.json({ error: "No conversation query provided" }, { status: 400 })
    }

    const apiKey = process.env.OPENAI_API_KEY

    if (!apiKey) {
      console.error("API: OpenAI API key not found in environment variables")
      return NextResponse.json({ error: "OpenAI API key not configured" }, { status: 500 })
    }

    console.log("API: OpenAI API key found, length:", apiKey.length)

    // Parse the conversation query if it's a string
    let queryData
    try {
      queryData = typeof conversationQuery === "string" ? JSON.parse(conversationQuery) : conversationQuery
      console.log("API: Parsed query data:", queryData)
    } catch (err) {
      console.log("API: Failed to parse as JSON, using as string")
      queryData = { content: conversationQuery }
    }

    // Extract the main content for summarization
    const contentToSummarize =
      queryData.sender_content ||
      queryData.email_content ||
      queryData.content ||
      queryData.sender_email_content ||
      JSON.stringify(queryData)

    console.log("API: Content to summarize:", contentToSummarize)

    const requestBody = {
      model: "gpt-4.1-mini",
      instructions:
        "You are a helpful assistant that summarizes customer service queries. Provide a clear, concise summary of the main issue or request.",
      input: `Please summarize this customer query in 2-3 sentences, focusing on the main issue or request:

${contentToSummarize}`,
    }

    console.log("API: Making request to OpenAI with body:", requestBody)

    const response = await fetch("https://api.openai.com/v1/responses", {
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

    // Extract the summary from the correct location in the response
    let summary = "Unable to generate summary"

    if (data.output && data.output.length > 0) {
      const firstOutput = data.output[0]
      if (firstOutput.content && firstOutput.content.length > 0) {
        const firstContent = firstOutput.content[0]
        if (firstContent.type === "output_text" && firstContent.text) {
          summary = firstContent.text
        }
      }
    }

    // Fallback to output_text if it exists (for different response formats)
    if (summary === "Unable to generate summary" && data.output_text) {
      summary = data.output_text
    }

    console.log("API: Extracted summary:", summary)

    return NextResponse.json({ summary })
  } catch (error) {
    console.error("API: Error generating summary:", error)
    return NextResponse.json(
      {
        error: `Failed to generate summary: ${error instanceof Error ? error.message : "Unknown error"}`,
      },
      { status: 500 },
    )
  }
}
