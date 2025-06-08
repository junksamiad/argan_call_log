"use client"

import { useState, useEffect } from "react"
import { marked } from "marked"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Loader2, Save, Edit3, CheckCircle, Layers } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"

interface WitSummaryEditorProps {
  isOpen: boolean
  onClose: () => void
  ticketNumber: string
  clientName: string
  careHomeName: string
}

export function WitSummaryEditor({ isOpen, onClose, ticketNumber, clientName, careHomeName }: WitSummaryEditorProps) {
  const [witSummary, setWitSummary] = useState("")
  const [editedSummary, setEditedSummary] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSavedMessage, setShowSavedMessage] = useState(false)

  useEffect(() => {
    if (isOpen && ticketNumber) {
      checkForExistingWitSummary()
      setShowSavedMessage(false)
    }
  }, [isOpen, ticketNumber])

  const checkForExistingWitSummary = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/check-wit-summary?ticketNumber=${encodeURIComponent(ticketNumber)}`)
      if (!response.ok) throw new Error(`Failed to check existing WiT summary: ${response.status}`)
      const result = await response.json()
      if (result.hasExistingSummary) {
        setWitSummary(result.existingSummary)
        setEditedSummary(result.existingSummary)
      } else {
        await generateNewWitSummary()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to check for existing WiT summary")
    } finally {
      setIsLoading(false)
    }
  }

  const generateNewWitSummary = async () => {
    setIsGenerating(true)
    setError(null)
    try {
      const dataResponse = await fetch(`/api/gather-ticket-data?ticketNumber=${encodeURIComponent(ticketNumber)}`)
      if (!dataResponse.ok) throw new Error(`Failed to gather ticket data: ${dataResponse.status}`)
      const dataResult = await dataResponse.json()

      const summaryResponse = await fetch("/api/generate-wit-summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticketData: dataResult.ticketData }),
      })
      const summaryResult = await summaryResponse.json()
      if (!summaryResponse.ok) throw new Error(summaryResult.error || `HTTP error: ${summaryResponse.status}`)

      setWitSummary(summaryResult.witSummary)
      setEditedSummary(summaryResult.witSummary)
      await saveToAirtable(summaryResult.witSummary)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate WiT summary")
    } finally {
      setIsGenerating(false)
    }
  }

  const saveToAirtable = async (summaryToSave: string) => {
    setIsSaving(true)
    try {
      const response = await fetch("/api/save-wit-summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticketNumber, witSummary: summaryToSave }),
      })
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `HTTP error: ${response.status}`)
      }
      setShowSavedMessage(true)
      setTimeout(() => setShowSavedMessage(false), 3000)
    } catch (err) {
      setError(`Failed to save WiT summary: ${err instanceof Error ? err.message : "Unknown error"}`)
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
    setWitSummary(editedSummary)
    setIsEditing(false)
  }

  const handleClose = () => {
    setWitSummary("")
    setEditedSummary("")
    setIsEditing(false)
    setError(null)
    setShowSavedMessage(false)
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[95vh] w-[95vw] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center">
            <Layers className="w-5 h-5 mr-2 text-purple-600" />
            WiT Summary (What, Why, Take)
          </DialogTitle>
          <DialogDescription>
            Concise AI-generated summary for ticket {ticketNumber} from {clientName} at {careHomeName}, based on Jon
            Moon's WiT model.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col space-y-4">
          {(isLoading || isGenerating) && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-4">
                <Loader2 className="w-8 h-8 animate-spin text-purple-600 mx-auto" />
                <p className="text-purple-600">
                  {isLoading ? "Loading WiT summary..." : "Generating concise WiT summary..."}
                </p>
                <p className="text-sm text-gray-500">
                  {isLoading ? "Checking for existing summary" : "Applying WiT model to ticket lifecycle..."}
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
                onClick={checkForExistingWitSummary}
                size="sm"
                variant="outline"
                className="mt-2 text-xs"
                disabled={isLoading || isGenerating}
              >
                Try Again
              </Button>
            </div>
          )}

          {witSummary && !isLoading && !isGenerating && (
            <div className="flex-1 overflow-hidden flex flex-col space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">AI-Generated WiT Summary</h3>
                <div className="flex gap-2">
                  {!isEditing ? (
                    <>
                      <Button
                        onClick={() => setIsEditing(true)}
                        variant="outline"
                        size="sm"
                        className="flex items-center gap-2"
                      >
                        <Edit3 className="w-4 h-4" /> Edit
                      </Button>
                      <Button
                        onClick={handleSave}
                        size="sm"
                        className="bg-green-600 hover:bg-green-700 text-white"
                        disabled={isSaving}
                      >
                        {isSaving ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Saving...
                          </>
                        ) : (
                          <>
                            <Save className="w-4 h-4 mr-2" /> Save
                          </>
                        )}
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button
                        onClick={() => {
                          setIsEditing(false)
                          setEditedSummary(witSummary)
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
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Saving...
                          </>
                        ) : (
                          <>
                            <Save className="w-4 h-4 mr-2" /> Save Changes
                          </>
                        )}
                      </Button>
                    </>
                  )}
                </div>
              </div>

              {showSavedMessage && (
                <div className="bg-green-50 border border-green-200 rounded-md p-3 flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  <span className="text-sm text-green-700 font-medium">WiT Summary saved!</span>
                </div>
              )}

              <div className="flex-1 overflow-hidden border border-gray-200 rounded-lg min-h-[500px] max-h-[500px]">
                {isEditing ? (
                  <Textarea
                    value={editedSummary}
                    onChange={(e) => setEditedSummary(e.target.value)}
                    className="w-full h-full resize-none border-0 focus:ring-0 font-mono text-sm overflow-y-auto min-h-[500px] max-h-[500px]"
                    placeholder="Edit your WiT summary here..."
                  />
                ) : (
                  <div className="h-[500px] overflow-y-auto bg-white">
                    <div className="p-4">
                      <div
                        className="prose prose-sm max-w-none"
                        dangerouslySetInnerHTML={{ __html: marked(editedSummary || witSummary) }}
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
