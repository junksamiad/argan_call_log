"use client"

import type React from "react"

import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

import { useEffect, useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { RefreshCw, MessageCircle, Search, Calendar, Clock, Loader2, FileText, Eye } from "lucide-react"
import { Input } from "@/components/ui/input"
// Add this import at the top
import { ReportGenerator } from "./report-generator"

interface AirtableRecord {
  id: string
  fields: Record<string, any>
  createdTime: string
}

interface ConversationMessage {
  message_id: string
  timestamp: string
  sender: string
  sender_name: string
  message_type: string
  source: string
  extracted_from: string | null
  subject: string
  body_text: string
  content_hash: string
  thread_position: number
  ai_summary?: string
  priority: string
}

interface StaffRecord {
  id: string
  name: string
}

interface TimeLogEntry {
  id: string
  entryNumber: string
  assignee: string
  description: string
  timeLogged: number
  formattedTime: string
  createdTime: string
}

interface TimeLogData {
  nextEntryNumber: number
  mainRecordId: string
  existingEntries: number
  staffRecords: StaffRecord[]
  timeLogEntries?: TimeLogEntry[]
  totalTimeLogged?: number
  formattedTotalTime?: string
}

// Add this interface near the top with the other interfaces
interface StatusOption {
  name: string
  color: string
}

// Update the FIELD_NAMES constant to match the new table structure
const FIELD_NAMES = {
  ticket: "ticket_number",
  sender: "original_sender",
  subject: "subject",
  status: "status",
  date: "created_at",
  conversationHistory: "final_conversation_history",
}

// Helper function to format dates
function formatDate(dateString: string | undefined): string {
  if (!dateString) return "—"
  try {
    const date = new Date(dateString)
    return date.toLocaleString()
  } catch (e) {
    return dateString
  }
}

// Helper function to format duration for Airtable (in seconds)
function formatDurationForAirtable(hours: number, minutes: number): number {
  return hours * 3600 + minutes * 60
}

export default function CallLogData() {
  const [records, setRecords] = useState<AirtableRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedConversation, setSelectedConversation] = useState<ConversationMessage[] | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [expandedRecords, setExpandedRecords] = useState<Set<string>>(new Set())

  const [timeLogModalOpen, setTimeLogModalOpen] = useState(false)
  const [selectedTicketForTimeLog, setSelectedTicketForTimeLog] = useState<AirtableRecord | null>(null)
  const [timeLogData, setTimeLogData] = useState<TimeLogData | null>(null)
  const [timeLogLoading, setTimeLogLoading] = useState(false)
  const [timeLogSaving, setTimeLogSaving] = useState(false)

  // View time log state
  const [viewTimeLogModalOpen, setViewTimeLogModalOpen] = useState(false)
  const [viewTimeLogLoading, setViewTimeLogLoading] = useState(false)
  const [viewTimeLogData, setViewTimeLogData] = useState<TimeLogData | null>(null)
  const [selectedTicketForViewTimeLog, setSelectedTicketForViewTimeLog] = useState<AirtableRecord | null>(null)

  // Form state
  const [assigneeId, setAssigneeId] = useState("")
  const [description, setDescription] = useState("")
  const [hours, setHours] = useState(0)
  const [minutes, setMinutes] = useState(0)

  // Add these state variables after the existing state declarations
  const [availableStatuses, setAvailableStatuses] = useState<string[]>([])
  const [updatingStatus, setUpdatingStatus] = useState<string | null>(null)

  // Add this state variable with the other state variables
  const [statusOptions, setStatusOptions] = useState<StatusOption[]>([])
  // Add this state variable with the other state variables
  const [isReportGeneratorOpen, setIsReportGeneratorOpen] = useState(false)

  const router = useRouter()
  const initialized = useRef(false)

  // Add this function to fetch status options
  const fetchStatusOptions = async () => {
    try {
      const response = await fetch("/api/update-status")
      if (response.ok) {
        const result = await response.json()
        setStatusOptions(result.statusOptions || [])
      }
    } catch (err) {
      console.error("Error fetching status options:", err)
    }
  }

  // Update the useEffect to call fetchStatusOptions
  useEffect(() => {
    if (initialized.current) return
    initialized.current = true
    fetchData()
    fetchStatusOptions()
  }, [])

  const fetchData = async () => {
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

      // Sort records by ticket_number if available, lowest first
      const sortedRecords = [...(result.records || [])].sort((a, b) => {
        const ticketA = a.fields[FIELD_NAMES.ticket]
          ? Number.parseInt(a.fields[FIELD_NAMES.ticket].toString().replace(/[^0-9]/g, ""))
          : 999999
        const ticketB = b.fields[FIELD_NAMES.ticket]
          ? Number.parseInt(b.fields[FIELD_NAMES.ticket].toString().replace(/[^0-9]/g, ""))
          : 999999
        return ticketA - ticketB // Sort in ascending order (lowest first)
      })

      setRecords(sortedRecords)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unknown error occurred"
      setError(errorMessage)
      console.error("Error fetching data:", err)
    } finally {
      setLoading(false)
    }
  }

  const fetchTimeLogData = async (ticketNumber: string, fetchEntries = false) => {
    try {
      setTimeLogLoading(true)
      const response = await fetch(
        `/api/time-log?ticketNumber=${encodeURIComponent(ticketNumber)}&fetchEntries=${fetchEntries}`,
      )

      if (!response.ok) {
        throw new Error(`Failed to fetch time log data: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (err) {
      console.error("Error fetching time log data:", err)
      alert("Failed to load time log data. Please try again.")
      return null
    } finally {
      setTimeLogLoading(false)
    }
  }

  const handleRefresh = () => {
    fetchData()
  }

  const handleOpenSearch = () => {
    router.push("/search")
  }

  const handleViewConversation = (record: AirtableRecord) => {
    try {
      // Try to parse the conversation history JSON
      const conversationField = record.fields["Conversation History"]
      if (!conversationField) {
        throw new Error("No conversation history available")
      }

      let conversation: ConversationMessage[]

      if (typeof conversationField === "string") {
        conversation = JSON.parse(conversationField)
      } else if (Array.isArray(conversationField)) {
        conversation = conversationField
      } else {
        throw new Error("Invalid conversation history format")
      }

      // Sort by thread_position or timestamp if available
      conversation.sort((a, b) => {
        if (a.thread_position && b.thread_position) {
          return a.thread_position - b.thread_position
        }
        return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      })

      setSelectedConversation(conversation)
      setIsDialogOpen(true)
    } catch (err) {
      console.error("Error parsing conversation history:", err)
      alert("Could not load conversation history. The data may be in an invalid format.")
    }
  }

  const handleOpenTimeLog = async (record: AirtableRecord, e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedTicketForTimeLog(record)
    setTimeLogModalOpen(true)

    // Reset form
    setAssigneeId("")
    setDescription("")
    setHours(0)
    setMinutes(0)
    setTimeLogData(null)

    // Fetch time log data for this ticket
    const ticketNumber = record.fields[FIELD_NAMES.ticket]
    if (ticketNumber) {
      const data = await fetchTimeLogData(ticketNumber)
      if (data) {
        setTimeLogData(data)
      }
    }
  }

  const handleViewTimeLog = async (record: AirtableRecord, e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedTicketForViewTimeLog(record)
    setViewTimeLogModalOpen(true)
    setViewTimeLogLoading(true)
    setViewTimeLogData(null)

    // Fetch time log entries for this ticket
    const ticketNumber = record.fields[FIELD_NAMES.ticket]
    if (ticketNumber) {
      try {
        const response = await fetch(`/api/time-log?ticketNumber=${encodeURIComponent(ticketNumber)}&fetchEntries=true`)

        if (!response.ok) {
          throw new Error(`Failed to fetch time log data: ${response.status}`)
        }

        const data = await response.json()
        console.log("Time log data received:", data) // Debug log
        setViewTimeLogData(data)
      } catch (err) {
        console.error("Error fetching time log data:", err)
        alert("Failed to load time log data. Please try again.")
      }
    }
    setViewTimeLogLoading(false)
  }

  const handleGenerateTimeLogReport = (record: AirtableRecord, e: React.MouseEvent) => {
    e.stopPropagation()
    alert("Generate Time Log Report functionality will be implemented soon!")
    // This will be connected to an AI report generator in the future
  }

  const handleCloseTimeLog = () => {
    setTimeLogModalOpen(false)
    setSelectedTicketForTimeLog(null)
    setTimeLogData(null)
    setAssigneeId("")
    setDescription("")
    setHours(0)
    setMinutes(0)
  }

  const handleCloseViewTimeLog = () => {
    setViewTimeLogModalOpen(false)
    setSelectedTicketForViewTimeLog(null)
    setViewTimeLogData(null)
  }

  const handleSaveTimeLog = async () => {
    if (!selectedTicketForTimeLog || !timeLogData) {
      alert("Missing ticket or time log data")
      return
    }

    if (!assigneeId || !description || (hours === 0 && minutes === 0)) {
      alert("Please fill in all fields and specify a time duration")
      return
    }

    try {
      setTimeLogSaving(true)

      const timeLoggedInSeconds = formatDurationForAirtable(hours, minutes)
      const ticketNumber = selectedTicketForTimeLog.fields[FIELD_NAMES.ticket]

      const response = await fetch("/api/time-log", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ticketNumber,
          assigneeId, // Now sending the record ID instead of name
          description,
          timeLogged: timeLoggedInSeconds,
          mainRecordId: timeLogData.mainRecordId,
          entryNumber: timeLogData.nextEntryNumber,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `HTTP error: ${response.status}`)
      }

      const result = await response.json()

      alert(`Time log entry #${timeLogData.nextEntryNumber} created successfully!`)
      handleCloseTimeLog()
    } catch (err) {
      console.error("Error saving time log:", err)
      alert(`Failed to save time log: ${err instanceof Error ? err.message : "Unknown error"}`)
    } finally {
      setTimeLogSaving(false)
    }
  }

  const fetchAvailableStatuses = async () => {
    try {
      const response = await fetch("/api/update-status")
      if (response.ok) {
        const result = await response.json()
        setAvailableStatuses(result.availableStatuses || [])
      }
    } catch (err) {
      console.error("Error fetching available statuses:", err)
    }
  }

  // Helper function to get background color for status
  const getStatusColor = (status: string) => {
    const option = statusOptions.find((opt) => opt.name === status)
    if (!option) return "bg-gray-100"

    switch (option.color) {
      case "yellow":
      case "yellowBright":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "red":
      case "orangeLight2":
        return "bg-red-100 text-red-800 border-red-200"
      case "green":
      case "greenBright":
        return "bg-green-100 text-green-800 border-green-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const handleStatusUpdate = async (ticketNumber: string, newStatus: string) => {
    try {
      setUpdatingStatus(ticketNumber)

      const response = await fetch("/api/update-status", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ticketNumber,
          newStatus,
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to update status: ${response.status}`)
      }

      // Refresh the data to show the updated status
      await fetchData()
    } catch (err) {
      console.error("Error updating status:", err)
      alert("Failed to update status. Please try again.")
    } finally {
      setUpdatingStatus(null)
    }
  }

  // Add this handler function
  const handleGenerateReport = () => {
    setIsReportGeneratorOpen(true)
  }

  if (loading) {
    return <CallLogSkeleton />
  }

  if (error) {
    return (
      <Card className="border-gray-300 bg-gray-100 shadow-sm">
        <CardContent className="pt-4">
          <div className="flex items-center text-gray-800 mb-2">
            <span className="text-lg font-medium">Error Loading Data</span>
          </div>
          <p className="mb-4 text-sm text-gray-700">{error}</p>
          <Button
            onClick={handleRefresh}
            variant="outline"
            size="sm"
            className="bg-white hover:bg-gray-50 border-gray-300"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4 px-2 sm:px-0">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-3 sm:p-4 bg-sky-400 rounded-lg border border-sky-300">
        <div>
          <h2 className="text-xl font-semibold text-white flex items-center">
            <MessageCircle className="w-5 h-5 mr-2 text-blue-100" /> Call Log Data
          </h2>
          <p className="text-sm text-blue-100">
            {records.length} record{records.length !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            onClick={handleOpenSearch}
            variant="outline"
            size="sm"
            className="self-start sm:self-auto transition-all hover:bg-sky-300 hover:shadow-sm border-white text-white hover:text-white bg-sky-500"
          >
            <Search className="w-4 h-4 mr-2" />
            Reports
          </Button>
          <Button
            onClick={handleRefresh}
            variant="outline"
            size="sm"
            className="self-start sm:self-auto transition-all hover:bg-sky-300 hover:shadow-sm border-white text-white hover:text-white bg-sky-500"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Column Headers */}
      <div className="hidden sm:grid grid-cols-[15%_20%_35%_15%_15%] gap-4 px-6 py-3 bg-gray-200 border border-gray-300 rounded-t-lg font-medium text-sm text-gray-700 uppercase tracking-wider">
        <div>Ticket</div>
        <div>Care Home</div>
        <div>Subject</div>
        <div>Status</div>
        <div>Date</div>
      </div>

      {/* Clickable Table Rows */}
      {records.length === 0 ? (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="pt-4">
            <p className="text-sm text-amber-800">No records found in the database.</p>
          </CardContent>
        </Card>
      ) : (
        <Card className="border border-gray-200 overflow-hidden shadow-sm rounded-t-none">
          <Accordion type="multiple" className="w-full">
            {records.map((record, index) => {
              const isEven = index % 2 === 0
              const ticketNumber = record.fields[FIELD_NAMES.ticket] || `#${index + 1}`
              const careHomeName = record.fields["care_home_name"] || "—"
              const subjectLine = record.fields[FIELD_NAMES.subject] || "—"
              const emailDate = formatDate(record.fields[FIELD_NAMES.date])

              return (
                <AccordionItem key={record.id} value={record.id} className="border-b border-gray-100 last:border-b-0">
                  <AccordionTrigger
                    className={`transition-all duration-200 hover:bg-gradient-to-r ${
                      isEven
                        ? "hover:from-gray-50 hover:to-slate-50 bg-white"
                        : "hover:from-slate-50 hover:to-gray-100 bg-gray-25"
                    } px-4 py-3 text-left`}
                  >
                    <div className="flex flex-col sm:grid sm:grid-cols-[15%_20%_35%_15%_15%] gap-2 sm:gap-4 w-full min-w-0 pr-4">
                      <div className="min-w-0 flex flex-col sm:block">
                        <div
                          className={`text-sm font-medium ${isEven ? "text-gray-700" : "text-slate-700"} bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-center`}
                        >
                          {ticketNumber}
                        </div>
                      </div>
                      <div className="min-w-0 flex flex-col sm:block">
                        <div className="text-sm text-gray-900 truncate font-medium">{careHomeName}</div>
                      </div>
                      <div className="min-w-0 flex flex-col sm:block">
                        <div className="text-sm text-gray-900 truncate font-medium">{subjectLine}</div>
                      </div>
                      <div className="min-w-0 flex flex-col sm:block flex justify-start">
                        <div onClick={(e) => e.stopPropagation()}>
                          <Select
                            value={record.fields[FIELD_NAMES.status] || ""}
                            onValueChange={(newStatus) =>
                              handleStatusUpdate(record.fields[FIELD_NAMES.ticket], newStatus)
                            }
                            disabled={updatingStatus === record.fields[FIELD_NAMES.ticket]}
                          >
                            <SelectTrigger
                              className={`w-full h-7 text-xs ${getStatusColor(record.fields[FIELD_NAMES.status] || "")}`}
                            >
                              <SelectValue placeholder="Select status..." />
                            </SelectTrigger>
                            <SelectContent>
                              {statusOptions.map((option) => (
                                <SelectItem
                                  key={option.name}
                                  value={option.name}
                                  className={`text-xs ${getStatusColor(option.name)}`}
                                >
                                  {option.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        {updatingStatus === record.fields[FIELD_NAMES.ticket] && (
                          <Loader2 className="w-3 h-3 animate-spin text-blue-600 mt-1" />
                        )}
                      </div>
                      <div className="min-w-0 flex flex-col sm:block">
                        <div className="text-sm text-gray-900 truncate font-medium">{emailDate}</div>
                      </div>
                    </div>
                  </AccordionTrigger>

                  <AccordionContent className="px-4 pb-4">
                    <div
                      className={`pt-2 border-t ${isEven ? "border-gray-200 bg-gradient-to-r from-gray-50 to-slate-50" : "border-slate-200 bg-gradient-to-r from-slate-50 to-gray-100"}`}
                    >
                      <div className="space-y-6 p-3 rounded-lg">
                        <div className="text-xs text-gray-500 mb-2 flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          Created: {formatDate(record.createdTime)} • 🎫 Ticket: {ticketNumber}
                        </div>

                        {/* Subject */}
                        <Card>
                          <CardContent className="pt-4">
                            <div className="text-sm font-medium text-gray-700 mb-2">Subject</div>
                            <div className="text-base text-gray-900 bg-gray-50 p-3 rounded border">
                              {record.fields[FIELD_NAMES.subject] || "No subject"}
                            </div>
                          </CardContent>
                        </Card>

                        {/* Conversation History */}
                        <Card>
                          <CardContent className="pt-4">
                            <div className="text-sm font-medium text-gray-700 mb-3">Conversation History</div>
                            {record.fields["conversation_history"] || record.fields["initial_conversation_query"] ? (
                              <ConversationHistory conversationData={record.fields} />
                            ) : (
                              <div className="text-sm text-gray-500 italic bg-gray-50 p-4 rounded border">
                                No conversation history available
                              </div>
                            )}
                          </CardContent>
                        </Card>

                        {/* Action Buttons */}
                        <div className="flex justify-end gap-2 pt-3">
                          <Button
                            onClick={(e) => handleViewTimeLog(record, e)}
                            variant="outline"
                            size="sm"
                            className="bg-blue-600 hover:bg-blue-700 text-white border-blue-600 hover:border-blue-700 transition-all"
                          >
                            <Eye className="w-4 h-4 mr-2" />
                            View Time Log
                          </Button>
                          <Button
                            onClick={(e) => handleOpenTimeLog(record, e)}
                            variant="outline"
                            size="sm"
                            className="bg-green-600 hover:bg-green-700 text-white border-green-600 hover:border-green-700 transition-all"
                          >
                            <Clock className="w-4 h-4 mr-2" />
                            Log Time
                          </Button>
                          <Button
                            onClick={(e) => handleGenerateTimeLogReport(record, e)}
                            variant="outline"
                            size="sm"
                            className="bg-purple-600 hover:bg-purple-700 text-white border-purple-600 hover:border-purple-700 transition-all"
                          >
                            <FileText className="w-4 h-4 mr-2" />
                            Generate Report
                          </Button>
                        </div>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              )
            })}
          </Accordion>
        </Card>
      )}

      {/* Time Log Modal */}
      <Dialog open={timeLogModalOpen} onOpenChange={setTimeLogModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Log Time Entry</DialogTitle>
            <DialogDescription>
              Record time spent on ticket {selectedTicketForTimeLog?.fields[FIELD_NAMES.ticket] || "N/A"}
              {timeLogData && (
                <span className="block mt-1 text-xs text-green-600">
                  Entry #{timeLogData.nextEntryNumber} • {timeLogData.existingEntries} existing entries
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          {timeLogLoading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              <span className="ml-2 text-blue-600">Loading time log data...</span>
            </div>
          ) : (
            <div className="space-y-4 p-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Assignee</label>
                <Select value={assigneeId} onValueChange={setAssigneeId}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select staff member..." />
                  </SelectTrigger>
                  <SelectContent>
                    {timeLogData?.staffRecords && timeLogData.staffRecords.length > 0 ? (
                      timeLogData.staffRecords.map((staff) => (
                        <SelectItem key={staff.id} value={staff.id}>
                          {staff.name}
                        </SelectItem>
                      ))
                    ) : (
                      <div className="px-2 py-1 text-sm text-gray-500">No staff records found</div>
                    )}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Time Logged</label>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <label className="text-xs text-gray-500">Hours</label>
                    <Input
                      type="number"
                      min="0"
                      max="12"
                      value={hours}
                      onChange={(e) => setHours(Number.parseInt(e.target.value) || 0)}
                      className="w-full"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-xs text-gray-500">Minutes</label>
                    <Input
                      type="number"
                      min="0"
                      max="59"
                      value={minutes}
                      onChange={(e) => setMinutes(Number.parseInt(e.target.value) || 0)}
                      className="w-full"
                    />
                  </div>
                </div>
                <div className="text-xs text-gray-500">
                  Total: {hours}h {minutes}m
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Description of Task</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-md text-sm"
                  rows={3}
                  placeholder="Describe the work performed..."
                />
              </div>

              <div className="flex justify-end space-x-2 pt-4">
                <Button variant="outline" onClick={handleCloseTimeLog} disabled={timeLogSaving}>
                  Cancel
                </Button>
                <Button
                  className="bg-green-600 hover:bg-green-700 text-white"
                  onClick={handleSaveTimeLog}
                  disabled={timeLogSaving || !assigneeId || !description || (hours === 0 && minutes === 0)}
                >
                  {timeLogSaving ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    "Save Time Entry"
                  )}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* View Time Log Modal */}
      <Dialog open={viewTimeLogModalOpen} onOpenChange={setViewTimeLogModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>Time Log Entries</DialogTitle>
            <DialogDescription>
              Time entries for ticket {selectedTicketForViewTimeLog?.fields[FIELD_NAMES.ticket] || "N/A"}
              {viewTimeLogData && viewTimeLogData.timeLogEntries && (
                <span className="block mt-1 text-xs text-blue-600">
                  {viewTimeLogData.timeLogEntries.length} entries • Total time: {viewTimeLogData.formattedTotalTime}
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          {viewTimeLogLoading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
              <span className="ml-2 text-blue-600">Loading time log entries...</span>
            </div>
          ) : (
            <div className="overflow-auto max-h-[calc(90vh-150px)]">
              {viewTimeLogData?.timeLogEntries && viewTimeLogData.timeLogEntries.length > 0 ? (
                <div className="space-y-4">
                  {/* Table Header */}
                  <div className="grid grid-cols-[80px_1fr_2fr_100px] gap-4 bg-gray-100 p-3 rounded-t-lg font-medium text-sm text-gray-700">
                    <div>Entry #</div>
                    <div>Assignee</div>
                    <div>Description</div>
                    <div>Time</div>
                  </div>

                  {/* Table Body */}
                  <div className="space-y-2">
                    {viewTimeLogData.timeLogEntries.map((entry) => (
                      <div
                        key={entry.id}
                        className="grid grid-cols-[80px_1fr_2fr_100px] gap-4 p-3 bg-white border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
                      >
                        <div className="text-sm font-medium text-gray-700">#{entry.entryNumber}</div>
                        <div className="text-sm text-gray-800">{entry.assignee}</div>
                        <div className="text-sm text-gray-800 whitespace-pre-wrap">{entry.description}</div>
                        <div className="text-sm font-medium text-gray-700">{entry.formattedTime}</div>
                      </div>
                    ))}
                  </div>

                  {/* Total Time */}
                  <div className="border-t border-gray-300 pt-4 mt-4">
                    <div className="flex justify-between items-center bg-gray-100 p-3 rounded-md">
                      <div className="font-medium text-gray-800">Total Time:</div>
                      <div className="font-bold text-gray-900">{viewTimeLogData.formattedTotalTime}</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center p-8 bg-gray-50 rounded-md border border-gray-200">
                  <p className="text-gray-600 font-medium mb-2">No time log entries found for this ticket.</p>
                  <p className="text-sm text-gray-500 mb-4">
                    Create your first time entry to start tracking time for this ticket.
                  </p>
                  <div className="flex flex-col gap-3 items-center">
                    <Button
                      onClick={(e) => {
                        handleCloseViewTimeLog()
                        if (selectedTicketForViewTimeLog) {
                          handleOpenTimeLog(selectedTicketForViewTimeLog, e as any)
                        }
                      }}
                      className="mt-2 bg-green-600 hover:bg-green-700 text-white"
                      size="sm"
                    >
                      <Clock className="w-4 h-4 mr-2" />
                      Create First Time Entry
                    </Button>
                    <Button
                      onClick={() => {
                        // Refresh the time log data
                        if (selectedTicketForViewTimeLog) {
                          handleViewTimeLog(selectedTicketForViewTimeLog, {} as any)
                        }
                      }}
                      className="bg-blue-600 hover:bg-blue-700 text-white"
                      size="sm"
                    >
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Refresh Time Log Data
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
      {/* Add this at the end of the component, just before the final closing tag */}
      <ReportGenerator isOpen={isReportGeneratorOpen} onClose={() => setIsReportGeneratorOpen(false)} />
    </div>
  )
}

function CallLogSkeleton() {
  return (
    <div className="space-y-4">
      <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-100">
        <Skeleton className="h-6 w-64 mb-1" />
        <Skeleton className="h-4 w-48" />
      </div>

      <div className="grid grid-cols-4 gap-4 px-6 py-3 bg-gray-50 border border-gray-200 rounded-t-lg">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-16" />
      </div>

      <Card className="border border-gray-200 rounded-t-none">
        <div className="space-y-0">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="border-b border-gray-100 last:border-b-0 p-4">
              <div className="grid grid-cols-4 gap-4 w-full">
                <Skeleton className="h-5 w-16" />
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-5 w-32" />
                <div className="flex justify-between items-center">
                  <Skeleton className="h-5 w-24" />
                  <Skeleton className="h-7 w-20" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

// Add the ConversationHistory component at the end of the file
function ConversationHistory({ conversationData }: { conversationData: any }) {
  // Parse the conversation_history field specifically
  const conversations = (() => {
    try {
      const historyField = conversationData.conversation_history || conversationData
      if (typeof historyField === "string") {
        return JSON.parse(historyField)
      } else if (Array.isArray(historyField)) {
        return historyField
      }
      return []
    } catch (err) {
      console.error("Error parsing conversation data:", err)
      return []
    }
  })()

  // Sort conversations by chronological_order (lowest first), then by thread_position, then by timestamp
  const sortedConversations = conversations.sort((a, b) => {
    // First priority: chronological_order (lowest first)
    if (a.chronological_order !== undefined && b.chronological_order !== undefined) {
      return a.chronological_order - b.chronological_order
    }
    // Second priority: thread_position
    if (a.thread_position && b.thread_position) {
      return a.thread_position - b.thread_position
    }
    // Third priority: timestamp
    return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  })

  if (!conversations.length && !conversationData.initial_conversation_query) {
    return <div className="text-sm text-gray-500 italic">No conversation entries found</div>
  }

  return (
    <Accordion type="multiple" className="w-full space-y-2">
      {/* Initial Conversation Query - Always First */}
      {conversationData.initial_conversation_query && (
        <AccordionItem
          key="initial-query"
          value="initial-query"
          className="border border-gray-200 rounded-lg overflow-hidden mb-3 shadow-sm"
        >
          <AccordionTrigger className="px-4 py-3 hover:bg-gray-100 text-left bg-gradient-to-r from-green-50 to-emerald-50 border-b border-gray-200">
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-green-200 flex items-center justify-center text-green-700 font-medium shadow-sm">
                  {(() => {
                    try {
                      const initialQueryData =
                        typeof conversationData.initial_conversation_query === "string"
                          ? JSON.parse(conversationData.initial_conversation_query)
                          : conversationData.initial_conversation_query

                      const senderName = initialQueryData?.sender_name || initialQueryData?.name
                      return senderName?.charAt(0)?.toUpperCase() || "I"
                    } catch (err) {
                      return "I"
                    }
                  })()}
                </div>
                <div>
                  <div className="font-medium">
                    {(() => {
                      try {
                        const initialQueryData =
                          typeof conversationData.initial_conversation_query === "string"
                            ? JSON.parse(conversationData.initial_conversation_query)
                            : conversationData.initial_conversation_query

                        return initialQueryData?.sender_name || initialQueryData?.name || "Initial Query"
                      } catch (err) {
                        return "Initial Query"
                      }
                    })()}
                  </div>
                  <div className="text-xs text-gray-500">
                    {(() => {
                      try {
                        const initialQueryData =
                          typeof conversationData.initial_conversation_query === "string"
                            ? JSON.parse(conversationData.initial_conversation_query)
                            : conversationData.initial_conversation_query

                        return initialQueryData?.sender_email_date || "No date"
                      } catch (err) {
                        return "No date"
                      }
                    })()}
                  </div>
                  <div className="text-xs text-gray-400 truncate max-w-[200px]">
                    {(() => {
                      try {
                        const initialQueryData =
                          typeof conversationData.initial_conversation_query === "string"
                            ? JSON.parse(conversationData.initial_conversation_query)
                            : conversationData.initial_conversation_query

                        return initialQueryData?.sender_email || "No email"
                      } catch (err) {
                        return "No email"
                      }
                    })()}
                  </div>
                </div>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4 pb-4 pt-2 bg-gray-50">
            <div className="space-y-3">
              {(() => {
                try {
                  const initialQueryData =
                    typeof conversationData.initial_conversation_query === "string"
                      ? JSON.parse(conversationData.initial_conversation_query)
                      : conversationData.initial_conversation_query

                  return Object.entries(initialQueryData)
                    .sort(([keyA], [keyB]) => {
                      // Prioritize sender name fields first
                      if (keyA.includes("sender_name") || keyA.includes("name")) return -1
                      if (keyB.includes("sender_name") || keyB.includes("name")) return 1

                      // Put content fields last
                      if (keyA.includes("content") || keyA.includes("email_content")) return 1
                      if (keyB.includes("content") || keyB.includes("email_content")) return -1

                      return 0
                    })
                    .map(([key, value]) => (
                      <div key={key} className="grid grid-cols-1 gap-2">
                        <div className="text-xs font-medium uppercase tracking-wide text-gray-600">
                          {key.replace(/_/g, " ")}:
                        </div>
                        <div className="text-sm bg-white p-2 rounded border border-gray-200 whitespace-pre-wrap">
                          {Array.isArray(value)
                            ? value.join(", ")
                            : typeof value === "object" && value !== null
                              ? JSON.stringify(value, null, 2)
                              : String(value || "N/A")}
                        </div>
                      </div>
                    ))
                } catch (err) {
                  return (
                    <div className="grid grid-cols-1 gap-2">
                      <div className="text-xs font-medium uppercase tracking-wide text-gray-600">
                        Initial Query Content:
                      </div>
                      <div className="text-sm bg-white p-3 rounded border border-gray-200 whitespace-pre-wrap max-h-96 overflow-y-auto">
                        {String(conversationData.initial_conversation_query) || "No initial query available"}
                      </div>
                    </div>
                  )
                }
              })()}
            </div>
          </AccordionContent>
        </AccordionItem>
      )}

      {/* Regular Conversation History */}
      {sortedConversations.map((conversation, index) => (
        <AccordionItem
          key={index}
          value={`conversation-${index}`}
          className="border border-gray-200 rounded-lg overflow-hidden mb-3 shadow-sm"
        >
          <AccordionTrigger className="px-4 py-3 hover:bg-gray-100 text-left bg-gradient-to-r from-sky-50 to-blue-50 border-b border-gray-200">
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-sky-200 flex items-center justify-center text-sky-700 font-medium shadow-sm">
                  {conversation.sender_name?.charAt(0)?.toUpperCase() || "U"}
                </div>
                <div>
                  <div className="font-medium">{conversation.sender_name || "Unknown Sender"}</div>
                  <div className="text-xs text-gray-500">{conversation.sender_email_date || "No date"}</div>
                  <div className="text-xs text-gray-400 truncate max-w-[200px]">
                    {conversation.sender_email || "No email"}
                  </div>
                </div>
              </div>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4 pb-4 pt-2 bg-gray-50">
            <div className="space-y-3">
              <div className="grid grid-cols-1 gap-2">
                <div className="text-xs font-medium uppercase tracking-wide text-gray-600">Sender Name:</div>
                <div className="text-sm bg-white p-2 rounded border border-gray-200">
                  {conversation.sender_name || "N/A"}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-2">
                <div className="text-xs font-medium uppercase tracking-wide text-gray-600">Sender Email:</div>
                <div className="text-sm bg-white p-2 rounded border border-gray-200">
                  {conversation.sender_email || "N/A"}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-2">
                <div className="text-xs font-medium uppercase tracking-wide text-gray-600">Sender Email Date:</div>
                <div className="text-sm bg-white p-2 rounded border border-gray-200">
                  {conversation.sender_email_date || "N/A"}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-2">
                <div className="text-xs font-medium uppercase tracking-wide text-gray-600">Sender Content:</div>
                <div className="text-sm bg-white p-3 rounded border border-gray-200 whitespace-pre-wrap max-h-96 overflow-y-auto">
                  {conversation.sender_content || "No content available"}
                </div>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  )
}
