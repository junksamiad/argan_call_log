"use client"

import { useState, useEffect } from "react"
import { marked } from "marked"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Loader2, Save, Edit3, CheckCircle } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"

interface HRSolutionEditorProps {
  isOpen: boolean
  onClose: () => void
  ticketNumber: string
  clientName: string
  careHomeName: string
  initialQuery: string
}

export function HRSolutionEditor({
  isOpen,
  onClose,
  ticketNumber,
  clientName,
  careHomeName,
  initialQuery,
}: HRSolutionEditorProps) {
  const [hrSolution, setHrSolution] = useState("")
  const [editedSolution, setEditedSolution] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSavedMessage, setShowSavedMessage] = useState(false)

  // Check for existing response when modal opens
  useEffect(() => {
    if (isOpen && ticketNumber) {
      checkForExistingResponse()
      setShowSavedMessage(false) // Reset saved message when opening
    }
  }, [isOpen, ticketNumber])

  const checkForExistingResponse = async () => {
    setIsLoading(true)
    setError(null)

    try {
      console.log("Checking for existing AI response for ticket:", ticketNumber)

      const response = await fetch(`/api/check-ai-response?ticketNumber=${encodeURIComponent(ticketNumber)}`)

      if (!response.ok) {
        throw new Error(`Failed to check existing response: ${response.status}`)
      }

      const result = await response.json()
      console.log("Check result:", result)

      if (result.hasExistingResponse) {
        // Load existing response
        console.log("Found existing response, loading it")
        setHrSolution(result.existingResponse)
        setEditedSolution(result.existingResponse)
      } else {
        // No existing response, generate new one
        console.log("No existing response found, generating new one")
        await generateNewHRSolution()
      }
    } catch (err) {
      console.error("Error checking for existing response:", err)
      setError(err instanceof Error ? err.message : "Failed to check for existing response")
    } finally {
      setIsLoading(false)
    }
  }

  const generateNewHRSolution = async () => {
    setIsGenerating(true)
    setError(null)

    try {
      console.log("Generating new HR solution for:", { ticketNumber, clientName, careHomeName })

      const response = await fetch("/api/generate-hr-solution", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          initialQuery,
        }),
      })

      console.log("Response status:", response.status)
      const result = await response.json()
      console.log("Response result:", result)

      if (!response.ok) {
        throw new Error(result.error || `HTTP error: ${response.status}`)
      }

      setHrSolution(result.hrSolution)
      setEditedSolution(result.hrSolution)

      // Automatically save the generated solution to Airtable
      await saveToAirtable(result.hrSolution)
    } catch (err) {
      console.error("Error generating HR solution:", err)
      const errorMessage = err instanceof Error ? err.message : "Failed to generate HR solution"
      setError(errorMessage)
    } finally {
      setIsGenerating(false)
    }
  }

  const saveToAirtable = async (solutionToSave: string) => {
    try {
      setIsSaving(true)

      const response = await fetch("/api/save-hr-solution", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ticketNumber,
          aiQueryResponse: solutionToSave,
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
      setTimeout(() => setShowSavedMessage(false), 3000) // Hide after 3 seconds
    } catch (err) {
      console.error("Error saving to Airtable:", err)
      // Show error in the existing error state instead of alert
      setError(`Failed to save: ${err instanceof Error ? err.message : "Unknown error"}`)
    } finally {
      setIsSaving(false)
    }
  }

  const handleSave = async () => {
    if (!editedSolution.trim()) {
      setError("No solution to save")
      return
    }

    setError(null) // Clear any existing errors
    await saveToAirtable(editedSolution)
    setHrSolution(editedSolution) // Update the original solution
    setIsEditing(false)
  }

  const handleClose = () => {
    setHrSolution("")
    setEditedSolution("")
    setIsEditing(false)
    setError(null)
    setShowSavedMessage(false)
    onClose()
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-6xl max-h-[95vh] w-[95vw] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>AI Response Editor</DialogTitle>
          <DialogDescription>
            Edit the AI-generated HR response for ticket {ticketNumber} from {clientName} at {careHomeName}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col space-y-4">
          {(isLoading || isGenerating) && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-4">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto" />
                <p className="text-blue-600">
                  {isLoading ? "Loading AI response..." : "Generating professional HR solution..."}
                </p>
                <p className="text-sm text-gray-500">
                  {isLoading ? "Checking for existing response" : "This may take a few moments"}
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
                onClick={checkForExistingResponse}
                size="sm"
                variant="outline"
                className="mt-2 text-xs"
                disabled={isLoading || isGenerating}
              >
                Try Again
              </Button>
            </div>
          )}

          {hrSolution && !isLoading && !isGenerating && (
            <div className="flex-1 overflow-hidden flex flex-col space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium">AI-Generated HR Response</h3>
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
                          setEditedSolution(hrSolution)
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
                    value={editedSolution}
                    onChange={(e) => setEditedSolution(e.target.value)}
                    className="w-full h-full resize-none border-0 focus:ring-0 font-mono text-sm overflow-y-auto min-h-[500px] max-h-[500px]"
                    placeholder="Edit your HR solution here..."
                  />
                ) : (
                  <div className="h-[500px] overflow-y-auto bg-white">
                    <div className="p-4">
                      <div
                        className="prose prose-sm max-w-none"
                        dangerouslySetInnerHTML={{ __html: marked(editedSolution || hrSolution) }}
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
