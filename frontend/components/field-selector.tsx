"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { RefreshCw, Settings } from "lucide-react"

interface AirtableRecord {
  id: string
  fields: Record<string, any>
  createdTime: string
}

export function FieldSelector() {
  const [availableFields, setAvailableFields] = useState<string[]>([])
  const [selectedFields, setSelectedFields] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  const fetchFields = async () => {
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

      // Extract all unique field names from the records
      const fieldSet = new Set<string>()
      result.records?.forEach((record: AirtableRecord) => {
        Object.keys(record.fields).forEach((field) => fieldSet.add(field))
      })

      const fields = Array.from(fieldSet).sort()
      setAvailableFields(fields)

      // Select all fields by default
      setSelectedFields(fields)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unknown error occurred"
      setError(errorMessage)
      console.error("Error fetching fields:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFields()
  }, [])

  const handleFieldToggle = (fieldName: string) => {
    setSelectedFields((prev) => (prev.includes(fieldName) ? prev.filter((f) => f !== fieldName) : [...prev, fieldName]))
  }

  const handleSelectAll = () => {
    setSelectedFields(availableFields)
  }

  const handleSelectNone = () => {
    setSelectedFields([])
  }

  const handleCreateUI = () => {
    if (selectedFields.length === 0) {
      alert("Please select at least one field to display.")
      return
    }

    // Navigate to the custom view page with selected fields as URL parameters
    const fieldsParam = encodeURIComponent(JSON.stringify(selectedFields))
    router.push(`/custom-view?fields=${fieldsParam}`)
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-1/3" />
          <Skeleton className="h-4 w-2/3" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="flex items-center space-x-2">
                <Skeleton className="h-4 w-4" />
                <Skeleton className="h-4 w-32" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="text-red-600">Error Loading Fields</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4">{error}</p>
          <Button onClick={fetchFields} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (availableFields.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No Fields Found</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4">No fields were found in your Airtable data.</p>
          <Button onClick={fetchFields} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Settings className="w-5 h-5 mr-2" />
          Select Fields to Display
        </CardTitle>
        <CardDescription>
          Choose which fields from your call log you want to include in your custom view.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Selection Controls */}
          <div className="flex gap-2">
            <Button onClick={handleSelectAll} variant="outline" size="sm">
              Select All
            </Button>
            <Button onClick={handleSelectNone} variant="outline" size="sm">
              Select None
            </Button>
            <div className="ml-auto text-sm text-gray-600">
              {selectedFields.length} of {availableFields.length} fields selected
            </div>
          </div>

          {/* Field Checkboxes */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {availableFields.map((fieldName) => (
              <div key={fieldName} className="flex items-center space-x-2">
                <Checkbox
                  id={fieldName}
                  checked={selectedFields.includes(fieldName)}
                  onCheckedChange={() => handleFieldToggle(fieldName)}
                />
                <label
                  htmlFor={fieldName}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer capitalize"
                >
                  {fieldName.replace(/_/g, " ")}
                </label>
              </div>
            ))}
          </div>

          {/* Create UI Button */}
          <div className="pt-4 border-t">
            <Button onClick={handleCreateUI} disabled={selectedFields.length === 0} className="w-full" size="lg">
              Create UI ({selectedFields.length} field{selectedFields.length !== 1 ? "s" : ""})
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
