"use client"

import { useEffect, useState, useRef } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ArrowLeft, RefreshCw, Calendar, Hash, Type, List, FileText, AlertCircle, MessageSquare } from "lucide-react"

interface AirtableRecord {
  id: string
  fields: Record<string, any>
  createdTime: string
}

// Helper function to determine data type icon
function getDataTypeIcon(value: any) {
  if (value === null || value === undefined) return <AlertCircle className="h-3 w-3" />
  if (Array.isArray(value)) return <List className="h-3 w-3" />
  if (typeof value === "number") return <Hash className="h-3 w-3" />
  if (typeof value === "object") return <FileText className="h-3 w-3" />
  if (typeof value === "string") {
    if (!isNaN(Date.parse(value)) && value.includes("-")) return <Calendar className="h-3 w-3" />
    return <Type className="h-3 w-3" />
  }
  return <Type className="h-3 w-3" />
}

// Helper function to get preview fields (first 3-4 most important fields)
function getPreviewFields(fields: string[], record: AirtableRecord) {
  const priorityFields = ["name", "title", "subject", "caller_name", "phone_number", "date", "time"]
  const availableFields = fields.filter((field) => record.fields[field] !== undefined && record.fields[field] !== null)

  // Get priority fields first, then fill with other available fields
  const preview = priorityFields.filter((field) => availableFields.includes(field))
  const remaining = availableFields.filter((field) => !priorityFields.includes(field))

  return [...preview, ...remaining].slice(0, 4)
}

export function CustomDataView() {
  const [records, setRecords] = useState<AirtableRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFields, setSelectedFields] = useState<string[]>([])

  const initialized = useRef(false)
  const searchParams = useSearchParams()
  const router = useRouter()

  useEffect(() => {
    if (initialized.current) return
    initialized.current = true

    const fieldsParam = searchParams.get("fields")
    if (!fieldsParam) {
      setError("No fields selected. Please go back and select fields to display.")
      setLoading(false)
      return
    }

    try {
      const fields = JSON.parse(decodeURIComponent(fieldsParam))
      setSelectedFields(fields)
      fetchData(fields)
    } catch (err) {
      console.error("Error parsing fields parameter:", err)
      setError("Invalid field selection. Please go back and try again.")
      setLoading(false)
    }
  }, [])

  const fetchData = async (fields = selectedFields) => {
    if (fields.length === 0) {
      setError("No fields selected. Please go back and select fields to display.")
      setLoading(false)
      return
    }

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

      setRecords(result.records || [])
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unknown error occurred"
      setError(errorMessage)
      console.error("Error fetching data:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleBackToConfig = () => {
    router.push("/")
  }

  const handleRefresh = () => {
    fetchData()
  }

  if (loading) {
    return <CustomViewSkeleton />
  }

  if (error) {
    return (
      <div className="space-y-4">
        <Button onClick={handleBackToConfig} variant="outline" className="transition-all hover:bg-gray-100">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Configuration
        </Button>
        <Card className="border-red-200 bg-red-50 shadow-sm">
          <CardHeader className="bg-red-100 border-b border-red-200">
            <CardTitle className="text-red-700 flex items-center text-sm">
              <AlertCircle className="w-4 h-4 mr-2" />
              Error Loading Data
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <p className="mb-4 text-sm text-red-700">{error}</p>
            <Button onClick={handleRefresh} variant="outline" size="sm" className="bg-white hover:bg-red-50">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4 px-2 sm:px-0">
      {/* Compact Header */}
      <div className="flex flex-col gap-3 p-3 sm:p-4 bg-gradient-to-r from-gray-100 to-slate-100 rounded-lg border border-gray-200">
        <div>
          <Button
            onClick={handleBackToConfig}
            variant="outline"
            size="sm"
            className="mb-3 transition-all hover:bg-white hover:shadow-sm border-gray-300"
          >
            <ArrowLeft className="w-4 h-4 mr-2 text-gray-600" />
            Back to Configuration
          </Button>
          <h2 className="text-xl font-semibold text-gray-800">📞 Call Log Data</h2>
          <p className="text-sm text-gray-600">
            {records.length} record{records.length !== 1 ? "s" : ""} • {selectedFields.length} field
            {selectedFields.length !== 1 ? "s" : ""}
          </p>
        </div>
        <Button
          onClick={handleRefresh}
          variant="outline"
          size="sm"
          className="self-start sm:self-auto transition-all hover:bg-white hover:shadow-sm border-gray-300 text-gray-700"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Compact Selected Fields */}
      <Card className="bg-gray-700 border-gray-600">
        <CardContent className="pt-3 pb-3">
          <div className="flex flex-wrap gap-1">
            <span className="text-xs text-gray-300 mr-2 font-medium">📋 Active Fields:</span>
            {selectedFields.map((field) => (
              <Badge
                key={field}
                variant="secondary"
                className="px-2 py-0.5 text-xs bg-gray-600 text-gray-200 border border-gray-500 hover:bg-gray-500 transition-colors"
              >
                {field.replace(/_/g, " ")}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Accordion Table */}
      {records.length === 0 ? (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="pt-4">
            <p className="text-sm text-amber-800">No records found in the database.</p>
          </CardContent>
        </Card>
      ) : (
        <Card className="border border-gray-200 overflow-hidden shadow-sm">
          <Accordion type="multiple" className="w-full">
            {records.map((record, index) => {
              const previewFields = getPreviewFields(selectedFields, record)
              const hasTranscript =
                record.fields.conversation_history || record.fields.transcript || record.fields.notes
              const isEven = index % 2 === 0

              return (
                <AccordionItem key={record.id} value={record.id} className="border-b border-gray-100 last:border-b-0">
                  <AccordionTrigger
                    className={`hover:bg-gradient-to-r ${isEven ? "hover:from-gray-50 hover:to-slate-50" : "hover:from-slate-50 hover:to-gray-100"} px-4 py-3 text-left transition-all duration-200`}
                  >
                    <div className="flex items-center justify-between w-full pr-4">
                      <div className="flex items-center space-x-4 min-w-0 flex-1">
                        <div className="flex-shrink-0">
                          <Badge
                            variant="outline"
                            className={`text-xs px-2 py-0.5 ${isEven ? "bg-gray-100 text-gray-700 border-gray-300" : "bg-slate-100 text-slate-700 border-slate-300"}`}
                          >
                            #{index + 1}
                          </Badge>
                        </div>

                        {/* Preview Data in Table Format */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 flex-1 min-w-0">
                          {previewFields.map((fieldName) => {
                            const value = record.fields[fieldName]
                            const displayValue = Array.isArray(value)
                              ? value.join(", ")
                              : typeof value === "object" && value !== null
                                ? "Object"
                                : value !== undefined && value !== null
                                  ? String(value)
                                  : "N/A"

                            return (
                              <div key={fieldName} className="min-w-0">
                                <div
                                  className={`text-xs uppercase tracking-wide truncate font-medium ${isEven ? "text-gray-600" : "text-slate-600"}`}
                                >
                                  {fieldName.replace(/_/g, " ")}
                                </div>
                                <div className="text-sm text-gray-900 truncate font-medium" title={displayValue}>
                                  {displayValue === "N/A" ? <span className="text-gray-400">—</span> : displayValue}
                                </div>
                              </div>
                            )
                          })}
                        </div>

                        {/* Transcript Button */}
                        <div className="flex-shrink-0 mt-2 sm:mt-0">
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button
                                variant="outline"
                                size="sm"
                                className="text-xs px-2 py-1 h-7 bg-gray-700 border-gray-600 text-white hover:bg-gray-600 transition-all"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <MessageSquare className="w-3 h-3 mr-1" />💬 Transcript
                              </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl max-h-[80vh]">
                              <DialogHeader>
                                <DialogTitle className="text-lg">Conversation Transcript</DialogTitle>
                                <DialogDescription className="text-sm">
                                  Record #{index + 1} • {new Date(record.createdTime).toLocaleString()}
                                </DialogDescription>
                              </DialogHeader>
                              <ScrollArea className="max-h-[60vh] w-full">
                                <div className="p-4 bg-gray-50 rounded-lg">
                                  <pre className="text-sm whitespace-pre-wrap text-gray-800">
                                    {record.fields.conversation_history ||
                                      record.fields.transcript ||
                                      record.fields.notes ||
                                      "No transcript available"}
                                  </pre>
                                </div>
                              </ScrollArea>
                            </DialogContent>
                          </Dialog>
                        </div>
                      </div>
                    </div>
                  </AccordionTrigger>

                  <AccordionContent className="px-4 pb-4">
                    <div
                      className={`pt-2 border-t ${isEven ? "border-gray-200 bg-gradient-to-r from-gray-50 to-slate-50" : "border-slate-200 bg-gradient-to-r from-slate-50 to-gray-100"}`}
                    >
                      <div className="grid gap-3 p-3 rounded-lg">
                        <div className="text-xs text-gray-500 mb-2 flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          Created: {new Date(record.createdTime).toLocaleString()} • 🆔 {record.id}
                        </div>

                        {/* All Fields */}
                        <div className="grid gap-3">
                          {selectedFields.map((fieldName) => {
                            const value = record.fields[fieldName]
                            const displayValue = Array.isArray(value)
                              ? value.join(", ")
                              : typeof value === "object" && value !== null
                                ? JSON.stringify(value, null, 2)
                                : value !== undefined && value !== null
                                  ? String(value)
                                  : "N/A"

                            return (
                              <div
                                key={fieldName}
                                className="grid grid-cols-1 gap-2 py-2 border-b border-gray-100 last:border-b-0"
                              >
                                <div
                                  className={`flex items-center gap-2 text-xs font-medium uppercase tracking-wide ${isEven ? "text-gray-600" : "text-slate-600"}`}
                                >
                                  <div
                                    className={`flex items-center justify-center w-4 h-4 rounded-full ${isEven ? "bg-gray-200 text-gray-600" : "bg-slate-200 text-slate-600"}`}
                                  >
                                    {getDataTypeIcon(value)}
                                  </div>
                                  {fieldName.replace(/_/g, " ")}
                                </div>
                                <div className="text-sm text-gray-900">
                                  {displayValue === "N/A" ? (
                                    <span className="text-gray-400 italic">N/A</span>
                                  ) : typeof value === "object" && value !== null ? (
                                    <pre className="text-xs bg-white p-2 rounded border border-gray-200 overflow-x-auto shadow-sm">
                                      {displayValue}
                                    </pre>
                                  ) : (
                                    <div className="bg-white p-2 rounded border border-gray-100 shadow-sm">
                                      {displayValue}
                                    </div>
                                  )}
                                </div>
                              </div>
                            )
                          })}
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
    </div>
  )
}

function CustomViewSkeleton() {
  return (
    <div className="space-y-4">
      <div>
        <Skeleton className="h-8 w-48 mb-3" />
        <Skeleton className="h-6 w-64 mb-1" />
        <Skeleton className="h-4 w-48" />
      </div>

      <Card>
        <CardContent className="pt-3 pb-3">
          <div className="flex flex-wrap gap-1">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-6 w-20" />
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <div className="space-y-0">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="border-b border-gray-100 last:border-b-0 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4 flex-1">
                  <Skeleton className="h-6 w-8" />
                  <div className="grid grid-cols-4 gap-2 flex-1">
                    <div>
                      <Skeleton className="h-3 w-16 mb-1" />
                      <Skeleton className="h-4 w-24" />
                    </div>
                    <div>
                      <Skeleton className="h-3 w-16 mb-1" />
                      <Skeleton className="h-4 w-20" />
                    </div>
                    <div>
                      <Skeleton className="h-3 w-16 mb-1" />
                      <Skeleton className="h-4 w-28" />
                    </div>
                    <div>
                      <Skeleton className="h-3 w-16 mb-1" />
                      <Skeleton className="h-4 w-16" />
                    </div>
                  </div>
                </div>
                <Skeleton className="h-6 w-20" />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
