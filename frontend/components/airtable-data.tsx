"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { RefreshCw } from "lucide-react"

interface AirtableRecord {
  id: string
  fields: Record<string, any>
  createdTime: string
}

interface AirtableResponse {
  records: AirtableRecord[]
  error?: string
  details?: any
}

export function AirtableData() {
  const [data, setData] = useState<AirtableResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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

      setData(result)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unknown error occurred"
      setError(errorMessage)
      console.error("Error fetching Airtable data:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) {
    return <AirtableDataSkeleton />
  }

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="text-red-600">Error Loading Data</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4">{error}</p>
          <Button onClick={fetchData} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!data || !data.records || data.records.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No Data Found</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4">No records were found in the Airtable database.</p>
          <Button onClick={fetchData} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <p className="text-sm text-gray-600">
          Showing {data.records.length} record{data.records.length !== 1 ? "s" : ""}
        </p>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {data.records.map((record) => (
        <Card key={record.id} className="overflow-hidden">
          <CardHeader className="bg-gray-50">
            <CardTitle className="text-lg">{record.id}</CardTitle>
            <CardDescription>Created: {new Date(record.createdTime).toLocaleString()}</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <dl className="grid gap-3">
              {Object.entries(record.fields).map(([key, value]) => (
                <div key={key} className="grid grid-cols-3 gap-2">
                  <dt className="col-span-1 font-medium text-gray-700 capitalize">{key.replace(/_/g, " ")}:</dt>
                  <dd className="col-span-2 text-gray-900">
                    {Array.isArray(value)
                      ? value.join(", ")
                      : typeof value === "object" && value !== null
                        ? JSON.stringify(value, null, 2)
                        : String(value || "N/A")}
                  </dd>
                </div>
              ))}
            </dl>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function AirtableDataSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(3)].map((_, i) => (
        <Card key={i} className="overflow-hidden">
          <CardHeader>
            <Skeleton className="h-6 w-1/3" />
            <Skeleton className="h-4 w-1/2" />
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full col-span-2" />
              </div>
              <div className="grid grid-cols-3 gap-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4 col-span-2" />
              </div>
              <div className="grid grid-cols-3 gap-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6 col-span-2" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
