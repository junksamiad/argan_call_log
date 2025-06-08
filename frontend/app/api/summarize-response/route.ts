import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { conversationHistory, bulletPoints = false, witModel = false } = await request.json()

    console.log("API: Received request with conversationHistory:", conversationHistory)

    if (!conversationHistory) {
      return NextResponse.json({ error: "No conversation history provided" }, { status: 400 })
    }

    const apiKey = process.env.OPENAI_API_KEY

    if (!apiKey) {
      console.error("API: OpenAI API key not found in environment variables")
      return NextResponse.json({ error: "OpenAI API key not configured" }, { status: 500 })
    }

    console.log("API: OpenAI API key found, length:", apiKey.length)

    // Parse the conversation history if it's a string
    let historyData
    try {
      historyData = typeof conversationHistory === "string" ? JSON.parse(conversationHistory) : conversationHistory
      console.log("API: Parsed conversation history:", historyData)
    } catch (err) {
      console.log("API: Failed to parse as JSON, using as string")
      historyData = conversationHistory
    }

    // Create the prompt for analyzing the response
    let promptInstructions = ""

    if (witModel) {
      promptInstructions = `Analyze this JSON and summarize the response to the original query using Jon Moon's WiT model:
      
1. WHAT: Clearly state the key findings or main points of the response
2. WHY: Explain the reasoning or evidence supporting these findings
3. TAKE: Provide the recommended actions or next steps

Format your summary with these three clear sections.`
    } else {
      promptInstructions = `Analyse this JSON and summarise the response to the original query that Sue (or an Argan Adviser) is suggesting.${bulletPoints ? " Format your summary as bullet points." : ""}`
    }

    const prompt = `${promptInstructions}

${JSON.stringify(historyData, null, 2)}`

    console.log("API: Prompt to send:", prompt)

    const requestBody = {
      model: "gpt-4.1-mini",
      instructions:
        "You are a helpful assistant that analyzes customer service conversations. Focus on summarizing the advice and solutions provided by the Argan HR consultants in response to the original customer query.",
      input: prompt,
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
    let summary = "Unable to generate response summary"

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
    if (summary === "Unable to generate response summary" && data.output_text) {
      summary = data.output_text
    }

    console.log("API: Extracted summary:", summary)

    return NextResponse.json({ summary })
  } catch (error) {
    console.error("API: Error generating response summary:", error)
    return NextResponse.json(
      {
        error: `Failed to generate response summary: ${error instanceof Error ? error.message : "Unknown error"}`,
      },
      { status: 500 },
    )
  }
}
