// frontend/components/DocumentUpload.tsx
'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import { Upload, FileUp, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { toast } from "sonner"

export default function DocumentUpload({ onUploadSuccess }: { onUploadSuccess: () => void }) {
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<{
    success: boolean;
    message: string;
  } | null>(null)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return

    setUploading(true)
    setUploadStatus(null)

    const formData = new FormData()
    formData.append('file', acceptedFiles[0])

    try {
      const response = await axios.post('http://localhost:8000/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setUploadStatus({
        success: true,
        message: `Successfully processed ${response.data.filename} with ${response.data.num_chunks} text chunks`,
      })
      
      toast(
        <div>
          <strong>Document Uploaded</strong>
          <div>Successfully processed {response.data.filename}</div>
        </div>
      )
      
      onUploadSuccess()
    } catch (error) {
      console.error('Upload error:', error)
      setUploadStatus({
        success: false,
        message: 'Error uploading document. Please try again.',
      })
      
      toast(
        <div>
          <strong>Upload Failed</strong>
          <div>There was an error uploading your document.</div>
        </div>,
        { className: "bg-destructive text-destructive-foreground" }
      )
    } finally {
      setUploading(false)
    }
  }, [onUploadSuccess, toast])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
  })

  return (
    <div className="w-full p-4">
      <Card>
        <CardContent className="pt-6">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition ${
              isDragActive ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-primary/50'
            }`}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center justify-center space-y-2">
              {isDragActive ? (
                <FileUp className="h-10 w-10 text-primary/70" />
              ) : (
                <Upload className="h-10 w-10 text-muted-foreground" />
              )}
              <p className="text-sm text-muted-foreground">
                {isDragActive
                  ? 'Drop the PDF here...'
                  : 'Drag & drop a PDF, or click to select'}
              </p>
              <p className="text-xs text-muted-foreground/70">Only PDF files are supported</p>
            </div>
          </div>

          {uploading && (
            <div className="mt-4 text-sm text-center text-muted-foreground">
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                <span>Uploading and processing document...</span>
              </div>
            </div>
          )}

          {uploadStatus && (
            <div className={`mt-4 p-3 rounded-lg text-sm flex items-center space-x-2 ${
              uploadStatus.success ? 'bg-green-50 text-green-700' : 'bg-destructive/10 text-destructive'
            }`}>
              {uploadStatus.success ? (
                <CheckCircle className="h-5 w-5" />
              ) : (
                <AlertCircle className="h-5 w-5" />
              )}
              <span>{uploadStatus.message}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}