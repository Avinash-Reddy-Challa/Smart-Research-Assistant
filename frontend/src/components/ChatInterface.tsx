// frontend/components/ChatInterface.tsx
'use client'

import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { Send } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"

type Message = {
  role: 'user' | 'assistant'
  content: string
  sources?: {
    source: string
    page: number
    snippet: string
  }[]
}

type ChatInterfaceProps = {
  initialMessages?: Message[]
  onMessagesChange?: (messages: Message[]) => void
}

export default function ChatInterface({ 
  initialMessages = [], 
  onMessagesChange 
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [showSources, setShowSources] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  

  // Scroll to bottom of messages when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  
  // Update messages when initialMessages changes
  useEffect(() => {
    if (initialMessages.length > 0) {
      setMessages(initialMessages)
    }
  }, [initialMessages])

  // Notify parent component when messages change
  useEffect(() => {
    onMessagesChange?.(messages)
  }, [messages, onMessagesChange])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    // Add user message
    const userMessage: Message = { role: 'user', content: input }
    const updatedMessages = [...messages, userMessage]
    setMessages(updatedMessages)
    setInput('')
    setLoading(true)

    try {
      // Send request to backend
      const response = await axios.post('http://localhost:8000/chat/', {
        question: input.trim(),
        include_sources: showSources,
      })

      // Add assistant message with sources
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.answer,
        sources: response.data.sources,
      }
      const finalMessages = [...updatedMessages, assistantMessage]
      setMessages(finalMessages)
    } catch (error) {
      console.error('Error getting response:', error)
      // Add error message
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, there was an error processing your question. Please try again.',
      }
      setMessages([...updatedMessages, errorMessage])
      
      toast.error("Error", { description: "Failed to get a response. Please try again." })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground mt-10">
            <p className="text-lg font-semibold">Ask a question about your documents</p>
            <p className="text-sm">
              For example: "What are the key findings in this research paper?" or "Summarize the main points of chapter 3"
            </p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <Card className={`max-w-3xl ${message.role === 'user' ? 'bg-primary text-primary-foreground' : ''}`}>
                <CardContent className="p-4">
                  <div className="prose prose-sm dark:prose-invert">
                    <ReactMarkdown>
                      {message.content}
                    </ReactMarkdown>
                  </div>

                  {/* Sources */}
                  {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border">
                      <p className="text-xs font-semibold text-muted-foreground mb-2">Sources:</p>
                      <div className="space-y-2">
                        {message.sources.map((source, idx) => (
                          <div key={idx} className="text-xs bg-muted p-2 rounded">
                            <div className="font-medium">{source.source} (Page {source.page + 1})</div>
                            <div className="text-muted-foreground mt-1 line-clamp-2">{source.snippet}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <Card>
              <CardContent className="p-4">
                <div className="flex space-x-2 items-center">
                  <div className="flex space-x-1">
                    <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce"></div>
                    <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="h-2 w-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                  <span className="text-sm text-muted-foreground ml-2">Thinking...</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-border p-4">
        <div className="flex items-center mb-3">
          <div className="flex items-center space-x-2">
            <Switch 
              id="show-sources"
              checked={showSources}
              onCheckedChange={setShowSources}
            />
            <Label htmlFor="show-sources" className="text-sm text-muted-foreground">
              Show sources in responses
            </Label>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="flex items-center space-x-2">
          <Input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about your documents..."
            className="flex-1"
            disabled={loading}
          />
          <Button type="submit" size="icon" disabled={loading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  )
}