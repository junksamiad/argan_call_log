"use client"

import { useState, useEffect } from "react"
import { marked } from "marked"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Loader2, Save, Edit3, CheckCircle } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"

interface AISummaryEditorProps {
  isOpen: boolean
  onClose: () => void
  ticketNumber: string
  clientName: string
  careHomeName: string
}

export function AISummaryEditor({ isOpen, onClose, ticketNumber, clientName, careHomeName }: AISummaryEditorProps) {
  const [aiSummary, setAiSummary] = useState("")
  const [editedSummary, setEditedSummary] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSavedMessage, setShowSavedMessage] = useState(false)

  // Check for existing summary when modal opens
  useEffect(() => {
    if (isOpen && ticketNumber) {
      checkForExistingSummary()
      setShowSavedMessage(false)
    }
  }, [isOpen, ticketNumber])

  const checkForExistingSummary = async () => {
    setIsLoading(true)
    setError(null)

    try {
      console.log("Checking for existing AI summary for ticket:", ticketNumber)

      const response = await fetch(`/api/check-ai-summary?ticketNumber=${encodeURIComponent(ticketNumber)}`)

      if (!response.ok) {
        throw new Error(`Failed to check existing summary: ${response.status}`)
      }

      const result = await response.json()
      console.log("Check result:", result)

      if (result.hasExistingSummary) {
        // Load existing summary
        console.log("Found existing summary, loading it")
        setAiSummary(result.existingSummary)
        setEditedSummary(result.existingSummary)
      } else {
        // No existing summary, generate new one
        console.log("No existing summary found, generating new one")
        await generateNewAISummary()
      }
    } catch (err) {
      console.error("Error checking for existing summary:", err)
      setError(err instanceof Error ? err.message : "Failed to check for existing summary")
    } finally {
      setIsLoading(false)
    }
  }

  const generateNewAISummary = async () => {
    setIsGenerating(true)
    setError(null)

    try {
      console.log("Gathering ticket data for:", { ticketNumber, clientName, careHomeName })

      // First gather all ticket data
      const dataResponse = await fetch(`/api/gather-ticket-data?ticketNumber=${encodeURIComponent(ticketNumber)}`)

      if (!dataResponse.ok) {
        throw new Error(`Failed to gather ticket data: ${dataResponse.status}`)
      }

      const dataResult = await dataResponse.json()
      console.log("Ticket data gathered:", dataResult)

      // Then generate AI summary
      const summaryResponse = await fetch("/api/generate-ai-summary", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ticketData: dataResult.ticketData,
        }),
      })

      console.log("Summary response status:", summaryResponse.status)
      const summaryResult = await summaryResponse.json()
      console.log("Summary result received")

      if (!summaryResponse.ok) {
        throw new Error(summaryResult.error || `HTTP error: ${summaryResponse.status}`)
      }

      setAiSummary(summaryResult.aiSummary)
      setEditedSummary(summaryResult.aiSummary)

      // Automatically save the generated summary to Airtable
      await saveToAirtable(summaryResult.aiSummary)
    } catch (err) {
      console.error("Error generating AI summary:", err)
      const errorMessage = err instanceof Error ? err.message : "Failed to generate AI summary"
      setError(errorMessage)
    } finally {
      setIsGenerating(false)
    }
  }

  const saveToAirtable = async (summaryToSave: string) => {
    try {
      setIsSaving(true)

      const response = await fetch("/api/save-ai-summary", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ticketNumber,
          aiSummary: summaryToSave,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `HTTP error: ${response.status}`)
      }

      const result = await response.json()
      console.log("Successfully saved to Airtable:", result)

      // Show success message
      setShowSavedMessage(true)
      setTimeout(() => setShowSavedMessage(false), 3000)
    } catch (err) {
      console.error("Error saving to Airtable:", err)
      setError(`Failed to save: ${err instanceof Error ? err.message : "Unknown error"}`)
    } finally {
      setIsSaving(false)
    }
  }

  const handleSave = async () => {
    if (!editedSummary.trim()) {
      setError("No summary to save")
      return
    }

    setError(null)
    await saveToAirtable(editedSummary)
    setAiSummary(editedSummary)
    setIsEditing(false)
  }

  const handleClose = () => {
    setAiSummary("")
    setEditedSummary("")
    setIsEditing(false)
    setError(null)
    setShowSavedMessage(false)
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-6xl max-h-[95vh] w-[95vw] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>AI Ticket Summary</DialogTitle>
          <DialogDescription>
            Comprehensive AI-generated lifecycle summary for ticket {ticketNumber} from {clientName} at {careHomeName}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col space-y-4">
          {(isLoading || isGenerating) && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-4">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto" />
                <p className="text-blue-600">
                  {isLoading ? "Loading ticket summary..." : "Generating comprehensive ticket summary..."}
                </p>
                <p className="text-sm text-gray-500">
                  {isLoading
                    ? "Checking for existing summary"
                    : "Analyzing ticket lifecycle, communications, and time logs"}
                </p>
                {isSaving && <p className="text-sm text-green-600">Saving to database...</p>}
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-700">
              <p className="font-medium">Error:</p>
              <p className="text-sm">{error}</p>
              <Button
                onClick={checkForExistingSummary}
                size="sm"
                variant="outline"
                className="mt-2 text-xs"
                disabled={isLoading || isGenerating}
              >
                Try Again
              </Button>
            </div>
          )}

          {aiSummary && !isLoading && !isGenerating && (
            <div className="flex-1 overflow-hidden flex flex-col space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">AI-Generated Ticket Summary</h3>
                <div className="flex gap-2">
                  {!isEditing ? (
                    <>
                      <Button
                        onClick={() => setIsEditing(true)}
                        variant="outline"
                        size="sm"
                        className="flex items-center gap-2"
                      >
                        <Edit3 className="w-4 h-4" />
                        Edit
                      </Button>
                      <Button
                        onClick={handleSave}
                        size="sm"
                        className="bg-green-600 hover:bg-green-700 text-white"
                        disabled={isSaving}
                      >
                        {isSaving ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="w-4 h-4 mr-2" />
                            Save
                          </>
                        )}
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button
                        onClick={() => {
                          setIsEditing(false)
                          setEditedSummary(aiSummary)
                        }}
                        variant="outline"
                        size="sm"
                      >
                        Cancel
                      </Button>
                      <Button
                        onClick={handleSave}
                        size="sm"
                        className="bg-green-600 hover:bg-green-700 text-white"
                        disabled={isSaving}
                      >
                        {isSaving ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="w-4 h-4 mr-2" />
                            Save Changes
                          </>
                        )}
                      </Button>
                    </>
                  )}
                </div>
              </div>

              {/* Success Message */}
              {showSavedMessage && (
                <div className="bg-green-50 border border-green-200 rounded-md p-3 flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  <span className="text-sm text-green-700 font-medium">Record saved...!</span>
                </div>
              )}

              <div className="flex-1 overflow-hidden border border-gray-200 rounded-lg min-h-[500px] max-h-[500px]">
                {isEditing ? (
                  <Textarea
                    value={editedSummary}
                    onChange={(e) => setEditedSummary(e.target.value)}
                    className="w-full h-full resize-none border-0 focus:ring-0 font-mono text-sm overflow-y-auto min-h-[500px] max-h-[500px]"
                    placeholder="Edit your AI summary here..."
                  />
                ) : (
                  <div className="h-[500px] overflow-y-auto bg-white">
                    <div className="p-4">
                      <div
                        className="prose prose-sm max-w-none"
                        dangerouslySetInnerHTML={{ __html: marked(editedSummary || aiSummary) }}
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="text-sm text-gray-500 text-center">
                {isEditing ? "Editing mode - Make your changes above" : "Preview mode - Click Edit to modify"}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
