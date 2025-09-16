// frontend/components/DocumentList.tsx
'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { File, RefreshCw, FileText } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { toast } from "sonner"

type Document = {
  filename: string
  num_pages: number
}

type DocumentListProps = {
  refresh: boolean
  onRefreshComplete: () => void
  onSummarize: (summary: string) => void
}

export default function DocumentList({ 
  refresh, 
  onRefreshComplete, 
  onSummarize 
}: DocumentListProps) {
  const [documents, setDocuments] = useState<Record<string, Document>>({})
  const [loading, setLoading] = useState(true)
  const [summarizing, setSummarizing] = useState<string | null>(null)
  const [summary, setSummary] = useState<string | null>(null)
  const [summaryDialogOpen, setSummaryDialogOpen] = useState(false)
  const [currentFile, setCurrentFile] = useState<string>("")

  const fetchDocuments = async () => {
    setLoading(true)
    try {
      const response = await axios.get('http://localhost:8000/documents/')
      setDocuments(response.data)
    } catch (error) {
      console.error('Error fetching documents:', error)
      toast.error("Error Loading Documents", {
        description: "Could not load your documents. Please try again.",
      })
    } finally {
      setLoading(false)
      onRefreshComplete()
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  useEffect(() => {
    if (refresh) {
      fetchDocuments()
    }
  }, [refresh])

  const handleSummarize = async (docId: string, filename: string) => {
    setSummarizing(docId)
    setCurrentFile(filename)
    try {
      const response = await axios.post(`http://localhost:8000/documents/${docId}/summarize`)
      const summaryText = response.data.summary
      setSummary(summaryText)
      setSummaryDialogOpen(true)
      onSummarize(summaryText)
    } catch (error) {
      console.error('Error summarizing document:', error)
      toast.error("Summarization Failed", {
        description: "Could not summarize the document. Please try again.",
      })
    } finally {
      setSummarizing(null)
    }
  }

  const documentCount = Object.keys(documents).length

  if (loading) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <RefreshCw className="animate-spin h-5 w-5 mx-auto mb-2" />
        <p>Loading documents...</p>
      </div>
    )
  }

  if (documentCount === 0) {
    return (
      <div className="p-4 text-center text-muted-foreground">
        <p>No documents uploaded yet</p>
      </div>
    )
  }

  return (
    <div className="p-4">
      <h3 className="text-sm font-medium mb-3">Uploaded Documents ({documentCount})</h3>
      <div className="space-y-2">
        {Object.entries(documents).map(([id, doc]) => (
          <Card key={id} className="overflow-hidden">
            <div className="p-3 flex items-center justify-between">
              <div className="flex items-center">
                <File className="h-4 w-4 text-muted-foreground mr-2" />
                <div className="text-sm">
                  <p className="font-medium truncate max-w-[150px]">{doc.filename}</p>
                  <p className="text-xs text-muted-foreground">{doc.num_pages} pages</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleSummarize(id, doc.filename)}
                disabled={summarizing === id}
                className="h-8 text-xs"
              >
                {summarizing === id ? (
                  <>
                    <RefreshCw className="mr-1 h-3 w-3 animate-spin" />
                    Summarizing...
                  </>
                ) : (
                  <>
                    <FileText className="mr-1 h-3 w-3" />
                    Summarize
                  </>
                )}
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {/* Summary Dialog */}
      <Dialog open={summaryDialogOpen} onOpenChange={setSummaryDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Document Summary</DialogTitle>
            <DialogDescription>
              Summary of {currentFile}
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 prose prose-sm max-h-[60vh] overflow-y-auto">
            {summary && summary.split('\n').map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}