"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Loader2, Download, FileText, Printer } from "lucide-react"
import { marked } from "marked"

interface ReportItem {
  id: string
  ticketNumber: string
  careHomeName: string
  subject: string
  status: string
  createdDate: string
  aiSummary: string
}

interface ReportGeneratorProps {
  isOpen: boolean
  onClose: () => void
}

export function ReportGenerator({ isOpen, onClose }: ReportGeneratorProps) {
  const [loading, setLoading] = useState(false)
  const [reportData, setReportData] = useState<ReportItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [generatingPDF, setGeneratingPDF] = useState(false)

  useEffect(() => {
    if (isOpen && reportData.length === 0 && !loading) {
      fetchReportData()
    }
  }, [isOpen, reportData.length, loading])

  const fetchReportData = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch("/api/generate-report")

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      setReportData(result.reportData || [])
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "An unknown error occurred"
      setError(errorMessage)
      console.error("Error fetching report data:", err)
    } finally {
      setLoading(false)
    }
  }

  const generatePDF = async () => {
    console.log("Generate PDF button clicked")
    setGeneratingPDF(true)
    setError(null)

    try {
      // Create a new window for printing
      const printWindow = window.open("", "_blank")

      if (!printWindow) {
        throw new Error("Could not open print window. Please allow popups for this site.")
      }

      // Generate the HTML content
      const htmlContent = generatePrintableHTML()

      // Write the content to the new window
      printWindow.document.write(htmlContent)
      printWindow.document.close()

      // Wait a moment for content to load, then trigger print
      setTimeout(() => {
        printWindow.print()
        printWindow.close()
      }, 1000)

      console.log("Print dialog opened successfully")
    } catch (err) {
      console.error("Error generating PDF:", err)
      setError(`Failed to generate PDF: ${err instanceof Error ? err.message : "Unknown error"}`)
    } finally {
      setGeneratingPDF(false)
    }
  }

  const generatePrintableHTML = () => {
    const reportHTML = reportData
      .map(
        (item) => `
      <div style="margin-bottom: 40px; padding-bottom: 30px; border-bottom: 1px solid #e5e7eb; page-break-inside: avoid;">
        <div style="margin-bottom: 16px;">
          <h3 style="font-size: 18px; font-weight: bold; color: #1f2937; margin-bottom: 8px;">
            Ticket #${item.ticketNumber} - ${item.subject}
          </h3>
          <div style="font-size: 14px; color: #6b7280;">
            <span>Care Home: ${item.careHomeName}</span>
            <span style="margin: 0 8px;">•</span>
            <span>Status: ${item.status}</span>
            <span style="margin: 0 8px;">•</span>
            <span>Created: ${new Date(item.createdDate).toLocaleDateString()}</span>
          </div>
        </div>
        <div style="font-size: 14px; line-height: 1.6; color: #374151;">
          ${marked(item.aiSummary)}
        </div>
      </div>
    `,
      )
      .join("")

    return `
      <!DOCTYPE html>
      <html>
        <head>
          <title>Argan Consultancy - AI Summaries Report</title>
          <style>
            @media print {
              body { margin: 0; }
              .no-print { display: none; }
            }
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              line-height: 1.6;
              color: #333;
              max-width: 800px;
              margin: 0 auto;
              padding: 20px;
            }
            h1, h2, h3, h4, h5, h6 {
              margin-top: 0;
              margin-bottom: 16px;
            }
            p {
              margin-bottom: 16px;
            }
            ul, ol {
              margin-bottom: 16px;
              padding-left: 24px;
            }
            li {
              margin-bottom: 4px;
            }
            strong {
              font-weight: 600;
            }
            code {
              background-color: #f3f4f6;
              padding: 2px 4px;
              border-radius: 3px;
              font-size: 0.9em;
            }
            pre {
              background-color: #f3f4f6;
              padding: 12px;
              border-radius: 6px;
              overflow-x: auto;
            }
            blockquote {
              border-left: 4px solid #e5e7eb;
              padding-left: 16px;
              margin: 16px 0;
              font-style: italic;
            }
          </style>
        </head>
        <body>
          <div style="text-align: center; margin-bottom: 40px;">
            <h1 style="font-size: 24px; font-weight: bold; color: #1f2937; margin-bottom: 8px;">
              Argan Consultancy
            </h1>
            <h2 style="font-size: 20px; font-weight: 600; color: #374151; margin-bottom: 8px;">
              AI Summaries Report
            </h2>
            <p style="color: #6b7280; margin-bottom: 0;">
              Generated on ${new Date().toLocaleDateString()}
            </p>
          </div>
          
          ${reportHTML}
          
          <div class="no-print" style="text-align: center; margin-top: 40px; padding: 20px; background-color: #f9fafb; border-radius: 8px;">
            <p style="margin: 0; color: #6b7280; font-size: 14px;">
              This report contains ${reportData.length} ticket${reportData.length !== 1 ? "s" : ""} with AI summaries.
            </p>
          </div>
        </body>
      </html>
    `
  }

  const downloadAsHTML = () => {
    console.log("Download HTML button clicked")
    try {
      const htmlContent = generatePrintableHTML()
      const blob = new Blob([htmlContent], { type: "text/html" })
      const url = URL.createObjectURL(blob)

      const a = document.createElement("a")
      a.href = url
      a.download = `argan-ai-summaries-report-${new Date().toISOString().split("T")[0]}.html`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      console.log("HTML file downloaded successfully")
    } catch (err) {
      console.error("Error downloading HTML:", err)
      setError(`Failed to download HTML: ${err instanceof Error ? err.message : "Unknown error"}`)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] w-[95vw] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>AI Summaries Report</DialogTitle>
          <DialogDescription>Comprehensive report of all AI summaries for tickets in the system</DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden flex flex-col space-y-4">
          {loading ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-4">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto" />
                <p className="text-blue-600">Generating report...</p>
                <p className="text-sm text-gray-500">Fetching AI summaries from all tickets</p>
              </div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-md p-4 text-red-700">
              <p className="font-medium">Error:</p>
              <p className="text-sm">{error}</p>
              <Button onClick={fetchReportData} size="sm" variant="outline" className="mt-2 text-xs">
                Try Again
              </Button>
            </div>
          ) : reportData.length === 0 ? (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center space-y-4">
                <FileText className="w-8 h-8 text-gray-400 mx-auto" />
                <p className="text-gray-600">No AI summaries found</p>
                <p className="text-sm text-gray-500">There are no tickets with AI summaries in the system.</p>
              </div>
            </div>
          ) : (
            <>
              <div className="flex justify-between items-center">
                <p className="text-sm text-gray-600">
                  Found {reportData.length} ticket{reportData.length !== 1 ? "s" : ""} with AI summaries
                </p>
                <div className="flex gap-2">
                  <Button onClick={downloadAsHTML} variant="outline" className="text-gray-700 border-gray-300">
                    <Download className="w-4 h-4 mr-2" />
                    Download HTML
                  </Button>
                  <Button
                    onClick={generatePDF}
                    className="bg-blue-600 hover:bg-blue-700 text-white"
                    disabled={generatingPDF}
                  >
                    {generatingPDF ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Opening Print...
                      </>
                    ) : (
                      <>
                        <Printer className="w-4 h-4 mr-2" />
                        Print Report
                      </>
                    )}
                  </Button>
                </div>
              </div>

              <div className="flex-1 overflow-auto border border-gray-200 rounded-lg bg-white p-6">
                <div id="report-content" className="max-w-3xl mx-auto">
                  <div className="text-center mb-8">
                    <h1 className="text-2xl font-bold text-gray-800">Argan Consultancy</h1>
                    <h2 className="text-xl font-semibold text-gray-700">AI Summaries Report</h2>
                    <p className="text-gray-500">Generated on {new Date().toLocaleDateString()}</p>
                  </div>

                  {reportData.map((item) => (
                    <div key={item.id} className="mb-10 pb-8 border-b border-gray-200">
                      <div className="mb-4">
                        <h3 className="text-lg font-bold text-gray-800">
                          Ticket #{item.ticketNumber} - {item.subject}
                        </h3>
                        <div className="flex flex-wrap gap-2 text-sm text-gray-600 mt-1">
                          <span>Care Home: {item.careHomeName}</span>
                          <span>•</span>
                          <span>Status: {item.status}</span>
                          <span>•</span>
                          <span>Created: {new Date(item.createdDate).toLocaleDateString()}</span>
                        </div>
                      </div>

                      <div className="prose prose-sm max-w-none">
                        <div dangerouslySetInnerHTML={{ __html: marked(item.aiSummary) }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
