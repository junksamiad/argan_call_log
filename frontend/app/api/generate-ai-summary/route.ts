import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { ticketData } = await request.json()

    console.log("API: Received request to generate AI summary for ticket:", ticketData.ticketInfo.ticketNumber)

    if (!ticketData) {
      return NextResponse.json({ error: "No ticket data provided" }, { status: 400 })
    }

    const apiKey = process.env.OPENAI_API_KEY

    if (!apiKey) {
      console.error("API: OpenAI API key not found in environment variables")
      return NextResponse.json({ error: "OpenAI API key not configured" }, { status: 500 })
    }

    // Create comprehensive prompt for AI summary
    const requestBody = {
      model: "gpt-4.1",
      messages: [
        {
          role: "system",
          content: `You are an expert business analyst specializing in HR consultancy case analysis. You create comprehensive, professional ticket lifecycle summaries for Argan HR Consultancy.

Your summaries should be:
- Comprehensive and detailed
- Professionally formatted in markdown
- Chronologically organized
- Include all key metrics and timelines
- Highlight important patterns and insights
- Use clear headings, bullet points, and tables where appropriate
- Professional tone suitable for management review

Format your response with clear markdown structure including headers, bullet points, tables, and emphasis where needed.`,
        },
        {
          role: "user",
          content: `Please create a comprehensive ticket lifecycle summary for the following HR consultancy case:

**TICKET DATA:**
${JSON.stringify(ticketData, null, 2)}

Please provide a detailed analysis that includes:

## 1. **Ticket Overview**
- Ticket number, care home, subject, current status
- Key dates and timeline overview

## 2. **Initial Query Analysis**
- Who submitted the query and when
- Care home details and contact information
- Nature of the HR issue/query

## 3. **Communication Timeline**
- Chronological breakdown of all communications
- Response times between client and Argan staff
- Key milestones in the conversation

## 4. **Argan Staff Involvement**
- Which Argan HR consultants were involved
- Their response times and communication patterns
- Quality and timeliness of responses

## 5. **Time Investment Analysis**
- Detailed breakdown of time logged by staff
- Tasks performed and time allocation
- Total time investment in the case

## 6. **Response Time Metrics**
- Initial response time from query to first Argan response
- Overall case resolution timeline
- Service level performance assessment

## 7. **Case Resolution Summary**
- Current status and outcomes
- Key decisions made and advice provided
- Client satisfaction indicators (if available)

## 8. **Key Insights & Recommendations**
- Notable patterns or issues identified
- Recommendations for process improvement
- Lessons learned for future similar cases

Please ensure the summary is professional, comprehensive, and suitable for management review. Use tables and formatting to make the information easily digestible.`,
        },
      ],
      temperature: 0.7,
      max_tokens: 3000,
    }

    console.log("API: Making request to OpenAI for summary generation")

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
    console.log("API: OpenAI response received")

    // Extract the summary from the response
    let aiSummary = "Unable to generate AI summary"

    if (data.choices && data.choices.length > 0 && data.choices[0].message) {
      aiSummary = data.choices[0].message.content
    }

    console.log("API: AI summary generated successfully")

    return NextResponse.json({ aiSummary })
  } catch (error) {
    console.error("API: Error generating AI summary:", error)
    return NextResponse.json(
      {
        error: `Failed to generate AI summary: ${error instanceof Error ? error.message : "Unknown error"}`,
      },
      { status: 500 },
    )
  }
}
