import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { ticketData } = await request.json()

    if (!ticketData) {
      return NextResponse.json({ error: "No ticket data provided" }, { status: 400 })
    }

    const apiKey = process.env.OPENAI_API_KEY
    if (!apiKey) {
      return NextResponse.json({ error: "OpenAI API key not configured" }, { status: 500 })
    }

    const requestBody = {
      model: "gpt-4.1", // Or your preferred model
      messages: [
        {
          role: "system",
          content: `You are an expert business analyst specializing in HR consultancy case analysis. You create concise, impactful ticket summaries for Argan HR Consultancy based on Jon Moon's WiT (What, Why, Take) model and Hierarchy of Information.

Your summaries MUST:
1.  Start with a **Headline/Executive Summary**: A single, impactful sentence summarizing the entire ticket lifecycle and outcome.
2.  Follow with the WiT structure:
    *   **WHAT**: Clearly and concisely state the key issue, events, and resolution.
    *   **WHY**: Briefly explain the reasons behind the key events or the significance of the outcome.
    *   **TAKE**: Outline the crucial actions taken, decisions made, or key takeaways/learnings.
3.  Be extremely concise and targeted for busy executives.
4.  Use professional language and clear markdown formatting (headings for Headline, WHAT, WHY, TAKE).
5.  Focus on clarity and impact.`,
        },
        {
          role: "user",
          content: `Please create a concise WiT summary for the following HR consultancy case, adhering to the Hierarchy of Information (Headline first, then WiT breakdown):

**TICKET DATA:**
${JSON.stringify(ticketData, null, 2)}

Ensure the summary is structured with:
- **Headline/Executive Summary**
- **WHAT**
- **WHY**
- **TAKE**`,
        },
      ],
      temperature: 0.5, // Lower temperature for more factual and concise output
      max_tokens: 1000, // Adjust as needed, but WiT should be concise
    }

    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(requestBody),
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { error: `OpenAI API error: ${response.status} - ${errorText}` },
        { status: response.status },
      )
    }

    const data = await response.json()
    let witSummary = "Unable to generate WiT summary"
    if (data.choices && data.choices.length > 0 && data.choices[0].message) {
      witSummary = data.choices[0].message.content
    }

    return NextResponse.json({ witSummary })
  } catch (error) {
    console.error("API: Error generating WiT summary:", error)
    return NextResponse.json(
      { error: `Failed to generate WiT summary: ${error instanceof Error ? error.message : "Unknown error"}` },
      { status: 500 },
    )
  }
}
