// frontend/app/page.tsx
'use client'

import { useState } from 'react'
import DocumentUpload from '../components/DocumentUpload'
import ChatInterface from '../components/ChatInterface'
import DocumentList from '../components/DocumentList'
import { Toaster } from "sonner"

type Message = {
  role: 'user' | 'assistant'
  content: string
  sources?: {
    source: string
    page: number
    snippet: string
  }[]
}

export default function Home() {
  const [refreshDocuments, setRefreshDocuments] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])

  const handleUploadSuccess = () => {
    setRefreshDocuments(true)
  }

  const handleRefreshComplete = () => {
    setRefreshDocuments(false)
  }

  const handleSummarize = (summary: string) => {
    // Create a new pair of messages for the summarization
    const newMessages: Message[] = [
      { role: 'user', content: 'Please summarize this document.' },
      { role: 'assistant', content: summary }
    ]
    
    setMessages(newMessages)
  }

  return (
    <main className="min-h-screen flex flex-col bg-muted/30">
      <header className="bg-background border-b border-border py-4">
        <div className="container mx-auto px-4">
          <h1 className="text-2xl font-bold">Smart Research Assistant</h1>
          <p className="text-muted-foreground">AI-Powered Knowledge Retrieval with RAG</p>
        </div>
      </header>

      <div className="flex-1 container mx-auto px-4 py-6 flex flex-col lg:flex-row gap-6">
        {/* Left sidebar */}
        <div className="w-full lg:w-80 flex flex-col gap-4">
          <DocumentUpload onUploadSuccess={handleUploadSuccess} />
          <div className="bg-background rounded-lg shadow-sm border border-border flex-1">
            <DocumentList 
              refresh={refreshDocuments} 
              onRefreshComplete={handleRefreshComplete} 
              onSummarize={handleSummarize}
            />
          </div>
        </div>

        {/* Main chat area */}
        <div className="flex-1 bg-background rounded-lg shadow-sm border border-border flex flex-col">
          <ChatInterface 
            initialMessages={messages} 
            onMessagesChange={setMessages}
          />
        </div>
      </div>
      
      <Toaster />
    </main>
  )
}