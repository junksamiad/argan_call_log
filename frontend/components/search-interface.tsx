"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Skeleton } from "@/components/ui/skeleton"
import { Send, Bot, User, MessageCircle, Calendar, RefreshCw, FileText, Brain, BarChart3, Layers } from "lucide-react"
import { useRouter } from "next/navigation"
import { HRSolutionEditor } from "./hr-solution-editor"
import { AISummaryEditor } from "./ai-summary-editor"
import { ReportGenerator } from "./report-generator"
import { WitSummaryEditor } from "./wit-summary-editor" // We'll create this next

interface ChatMessage {
  id: string
  type: "user" | "assistant"
  content: string
  timestamp: Date
}

interface AirtableRecord {
  id: string
  fields: Record<string, any>
  createdTime: string
}

interface TicketSummary {
  id: string
  ticketNumber: string
  careHomeName: string
  openerName: string
  subject: string
  status: string
  createdDate: string
  initialConversationQuery?: any
}

export function SearchInterface() {
  const router = useRouter()
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      type: "assistant",
      content:
        "Hello! I'm your AI assistant for the Argan Consultancy call log system. I can help you search, filter, and analyze your call data. What would you like to know?",
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = useState("")
  const [tickets, setTickets] = useState<TicketSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // HR Solution Editor state
  const [isHRSolutionEditorOpen, setIsHRSolutionEditorOpen] = useState(false)
  const [selectedTicketForHRSolution, setSelectedTicketForHRSolution] = useState<TicketSummary | null>(null)

  // AI Summary Editor state
  const [isAISummaryEditorOpen, setIsAISummaryEditorOpen] = useState(false)
  const [selectedTicketForAISummary, setSelectedTicketForAISummary] = useState<TicketSummary | null>(null)

  // Report Generator state
  const [isReportGeneratorOpen, setIsReportGeneratorOpen] = useState(false)

  // Add new state for WiT Summary Editor
  const [isWitSummaryEditorOpen, setIsWitSummaryEditorOpen] = useState(false)
  const [selectedTicketForWitSummary, setSelectedTicketForWitSummary] = useState<TicketSummary | null>(null)

  useEffect(() => {
    fetchTickets()
  }, [])

  const fetchTickets = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch("/api/airtable", {
        cache: "no-store",
      })

      const result = await response.json()

      if (!response.ok) {
        throw new Error(result.error || `HTTP error! status: ${response.status}`)
      }

      // Process records into ticket summaries
      const ticketSummaries: TicketSummary[] =
        result.records?.map((record: AirtableRecord) => {
          // Extract opener name from initial_conversation_query
          let openerName = "Unknown"
          try {
            const initialQuery = record.fields.initial_conversation_query
            if (initialQuery) {
              const queryData = typeof initialQuery === "string" ? JSON.parse(initialQuery) : initialQuery
              openerName = queryData?.sender_name || queryData?.name || "Unknown"
            }
          } catch (err) {
            console.error("Error parsing initial query:", err)
          }

          return {
            id: record.id,
            ticketNumber: record.fields.ticket_number || "N/A",
            careHomeName: record.fields.care_home_name || "Unknown Care Home",
            openerName,
            subject: record.fields.subject || "No Subject",
            status: record.fields.status || "unknown",
            createdDate: record.fields.created_at || record.createdTime,
            initialConversationQuery: record.fields.initial_conversation_query,
          }
        }) || []

      // Sort by ticket number (lowest first)
      const sortedTickets = ticketSummaries.sort((a, b) => {
        const ticketA = Number.parseInt(a.ticketNumber.toString().replace(/[^0-9]/g, "")) || 999999
        const ticketB = Number.parseInt(b.ticketNumber.toString().replace(/[^0-9]/g, "")) || 999999
        return ticketA - ticketB
      })

      setTickets(sortedTickets)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unknown error occurred"
      setError(errorMessage)
      console.error("Error fetching tickets:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = () => {
    if (!inputValue.trim()) return

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, newMessage])
    setInputValue("")

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content:
          "I understand you're looking for information. This AI interface is not yet connected to any backend services, but when implemented, I'll be able to help you search and analyze your call log data.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, aiResponse])
    }, 1000)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString()
    } catch {
      return "Unknown Date"
    }
  }

  const handleAIResponse = async (ticket: TicketSummary) => {
    if (!ticket.initialConversationQuery) {
      alert("No conversation query available for this ticket.")
      return
    }

    setSelectedTicketForHRSolution(ticket)
    setIsHRSolutionEditorOpen(true)
  }

  const handleAISummary = (ticket: TicketSummary) => {
    setSelectedTicketForAISummary(ticket)
    setIsAISummaryEditorOpen(true)
  }

  const handleGenerateReport = () => {
    setIsReportGeneratorOpen(true)
  }

  const handleWitSummary = (ticket: TicketSummary) => {
    setSelectedTicketForWitSummary(ticket)
    setIsWitSummaryEditorOpen(true)
  }

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-12rem)] bg-gray-50 p-4 lg:p-6">
      {/* Main Content Area - Left Side */}
      <div className="flex-1 flex flex-col min-w-0">
        {" "}
        {/* Added min-w-0 for flex child */}
        {/* "All Tickets" Header */}
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 bg-sky-400 rounded-t-lg border border-sky-300 p-4">
          {" "}
          {/* Removed mb-4, added rounded-t-lg */}
          <div>
            <h2 className="text-xl font-semibold text-white flex items-center">
              <MessageCircle className="w-5 h-5 mr-2 text-blue-100" />
              All Tickets ({tickets.length})
            </h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              onClick={handleGenerateReport}
              variant="outline"
              size="sm"
              className="transition-all hover:bg-sky-300 hover:shadow-sm border-white text-white hover:text-white bg-sky-500"
            >
              <FileText className="w-4 h-4 mr-2" />
              Generate Report
            </Button>
          </div>
        </div>
        {/* Tickets List Card */}
        <Card className="flex-1 border border-gray-200 shadow-sm overflow-hidden rounded-b-lg rounded-t-none">
          {" "}
          {/* Added rounded-b-lg, rounded-t-none */}
          <CardContent className="p-0 h-full overflow-hidden">
            {" "}
            {/* Changed to h-full */}
            {loading ? (
              // ... Skeleton remains the same
              <div className="p-4 space-y-4">
                {[...Array(8)].map((_, i) => (
                  <div key={i} className="flex items-center space-x-4 p-4 border-b border-gray-100">
                    <Skeleton className="h-10 w-16" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-48" />
                      <Skeleton className="h-3 w-32" />
                    </div>
                    <Skeleton className="h-6 w-20" />
                  </div>
                ))}
              </div>
            ) : error ? (
              // ... Error state remains the same
              <div className="p-6 text-center">
                <p className="text-red-600 mb-4">{error}</p>
                <Button onClick={fetchTickets} variant="outline" size="sm">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again
                </Button>
              </div>
            ) : (
              <ScrollArea className="h-full">
                {" "}
                {/* Ensure ScrollArea takes full height of its parent */}
                <div className="divide-y divide-gray-100">
                  {tickets.map((ticket) => (
                    <div
                      key={ticket.id}
                      className="p-4 hover:bg-gray-50 transition-colors cursor-pointer border-l-4 border-transparent hover:border-l-blue-400 relative"
                      onClick={() => router.push(`/?ticket=${ticket.ticketNumber}`)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4 flex-1 min-w-0">
                          {/* Ticket Number */}
                          <div className="flex-shrink-0">
                            <div className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full text-xs font-medium">
                              #{ticket.ticketNumber}
                            </div>
                          </div>

                          {/* Main Info */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-3 mb-1">
                              <h3 className="text-sm font-medium text-gray-900 truncate">{ticket.subject}</h3>
                            </div>
                            <div className="flex flex-wrap items-center gap-2 sm:space-x-4 text-xs text-gray-500">
                              <span className="flex items-center">
                                <span className="font-medium">Care Home:</span>
                                <span className="ml-1">{ticket.careHomeName}</span>
                              </span>
                              <span className="flex items-center">
                                <span className="font-medium">Opened by:</span>
                                <span className="ml-1">{ticket.openerName}</span>
                              </span>
                              <span className="flex items-center">
                                <Calendar className="w-3 h-3 mr-1" />
                                {formatDate(ticket.createdDate)}
                              </span>
                            </div>
                          </div>

                          {/* AI Buttons */}
                          <div className="flex-shrink-0 flex flex-col sm:flex-row gap-2 mt-2 sm:mt-0">
                            <Button
                              variant="outline"
                              size="sm"
                              className="text-xs h-7 px-2 bg-green-600 hover:bg-green-700 text-white border-green-600"
                              onClick={(e) => {
                                e.stopPropagation()
                                e.preventDefault()
                                handleAIResponse(ticket)
                              }}
                              disabled={!ticket.initialConversationQuery}
                              title="Generate detailed HR Solution"
                            >
                              <Brain className="w-3 h-3 mr-1" />
                              AI Response
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="text-xs h-7 px-2 bg-sky-600 hover:bg-sky-700 text-white border-sky-600"
                              onClick={(e) => {
                                e.stopPropagation()
                                e.preventDefault()
                                handleAISummary(ticket)
                              }}
                              title="Generate comprehensive AI Lifecycle Summary"
                            >
                              <BarChart3 className="w-3 h-3 mr-1" />
                              AI Summary
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="text-xs h-7 px-2 bg-purple-600 hover:bg-purple-700 text-white border-purple-600"
                              onClick={(e) => {
                                e.stopPropagation()
                                e.preventDefault()
                                handleWitSummary(ticket)
                              }}
                              title="Generate concise WiT Summary"
                            >
                              <Layers className="w-3 h-3 mr-1" />
                              WiT Summary
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Chatbot Widget - Right Side */}
      <div className="w-full lg:w-96 bg-white border border-gray-200 flex flex-col shadow-lg rounded-lg">
        {" "}
        {/* Removed mx-4, lg:mr-6, mb-6, max-h-96, lg:max-h-none. Increased lg:w-96 */}
        {/* Chat Header */}
        <div className="bg-sky-400 text-white p-4 flex items-center rounded-t-lg">
          <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center mr-3">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-medium">AI Assistant</h3>
            <p className="text-xs text-blue-100">Online • Ready to help</p>
          </div>
        </div>
        {/* Messages Area */}
        <div className="flex-1 overflow-hidden min-h-0">
          {" "}
          {/* Added min-h-0 for flex child */}
          <ScrollArea className="h-full p-4">
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${message.type === "user" ? "justify-end" : "justify-start"}`}
                >
                  {message.type === "assistant" && (
                    <Avatar className="w-7 h-7 border border-gray-200">
                      <AvatarFallback className="bg-blue-100 text-blue-700 text-xs">
                        <Bot className="w-4 h-4" />
                      </AvatarFallback>
                    </Avatar>
                  )}

                  <div
                    className={`max-w-[75%] rounded-lg px-3 py-2 text-sm ${
                      message.type === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-800 border border-gray-200"
                    }`}
                  >
                    <p>{message.content}</p>
                    <p className={`text-xs mt-1 ${message.type === "user" ? "text-blue-100" : "text-gray-500"}`}>
                      {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </div>

                  {message.type === "user" && (
                    <Avatar className="w-7 h-7 border border-gray-300">
                      <AvatarFallback className="bg-gray-200 text-gray-700 text-xs">
                        <User className="w-4 h-4" />
                      </AvatarFallback>
                    </Avatar>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
        {/* Input Area */}
        <div className="border-t border-gray-200 p-3">
          <div className="flex gap-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything..."
              className="flex-1 text-sm"
              size="sm"
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              size="sm"
              className="bg-blue-600 hover:bg-blue-700 text-white px-3"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* HR Solution Editor */}
      {selectedTicketForHRSolution && (
        <HRSolutionEditor
          isOpen={isHRSolutionEditorOpen}
          onClose={() => {
            setIsHRSolutionEditorOpen(false)
            setSelectedTicketForHRSolution(null)
          }}
          ticketNumber={selectedTicketForHRSolution.ticketNumber}
          clientName={selectedTicketForHRSolution.openerName}
          careHomeName={selectedTicketForHRSolution.careHomeName}
          initialQuery={selectedTicketForHRSolution.initialConversationQuery}
        />
      )}

      {/* AI Summary Editor */}
      {selectedTicketForAISummary && (
        <AISummaryEditor
          isOpen={isAISummaryEditorOpen}
          onClose={() => {
            setIsAISummaryEditorOpen(false)
            setSelectedTicketForAISummary(null)
          }}
          ticketNumber={selectedTicketForAISummary.ticketNumber}
          clientName={selectedTicketForAISummary.openerName}
          careHomeName={selectedTicketForAISummary.careHomeName}
        />
      )}

      {/* Report Generator */}
      <ReportGenerator isOpen={isReportGeneratorOpen} onClose={() => setIsReportGeneratorOpen(false)} />

      {/* WiT Summary Editor */}
      {selectedTicketForWitSummary && (
        <WitSummaryEditor
          isOpen={isWitSummaryEditorOpen}
          onClose={() => {
            setIsWitSummaryEditorOpen(false)
            setSelectedTicketForWitSummary(null)
          }}
          ticketNumber={selectedTicketForWitSummary.ticketNumber}
          clientName={selectedTicketForWitSummary.openerName}
          careHomeName={selectedTicketForWitSummary.careHomeName}
        />
      )}
    </div>
  )
}
