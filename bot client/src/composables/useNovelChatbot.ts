import { ref, onMounted } from "vue";
import axios from "axios";

interface Reference {
  page: number;
  startLine: number;
  endLine: number;
  content: string;
}

interface Message {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  references?: Reference[];
  timestamp: Date;
}

interface ProcessingStatus {
  status: "idle" | "processing" | "completed" | "error";
  progress: number;
  total_chunks: number;
  processed_chunks: number;
  current_document: string | null;
}

interface Document {
  id: string;
  filename: string;
}

export function useNovelChatbot() {
  const messages = ref<Message[]>([]);
  const isLoading = ref(false);
  const novelLoaded = ref(false);
  const isProcessing = ref(false);
  const currentDocumentId = ref<string | null>(null);
  const documents = ref<Document[]>([]);
  const uploadProgress = ref(0);

  // Create an axios instance for the Python backend
  const api = axios.create({
    baseURL: "http://localhost:8000",
    timeout: 30000,
  });

  // Status check interval
  let statusCheckIntervalId: number | undefined;

  // Monitor document processing status
  const checkProcessingStatus = async (): Promise<ProcessingStatus> => {
    try {
      const response = await api.get("/status");
      const status = response.data;

      // Update processing state based on status
      if (status.status === "completed") {
        isProcessing.value = false;
        novelLoaded.value = true;
        uploadProgress.value = 100;
        messages.value.push({
          id: Date.now(),
          role: "system",
          content: "Document processing completed successfully!",
          timestamp: new Date(),
        });
        stopStatusCheck();
      } else if (status.status === "error") {
        isProcessing.value = false;
        uploadProgress.value = 0;
        messages.value.push({
          id: Date.now(),
          role: "system",
          content: "Error processing document.",
          timestamp: new Date(),
        });
        stopStatusCheck();
      } else if (status.status === "processing") {
        isProcessing.value = true;
        if (status.progress !== undefined) {
          uploadProgress.value = status.progress;
        }
      }

      return status;
    } catch (error) {
      console.error("Error checking status:", error);
      throw error;
    }
  };

  // Start status monitoring
  const startStatusCheck = () => {
    if (!statusCheckIntervalId) {
      statusCheckIntervalId = window.setInterval(async () => {
        await checkProcessingStatus();
      }, 2000);
    }
  };

  // Stop status monitoring
  const stopStatusCheck = () => {
    if (statusCheckIntervalId) {
      window.clearInterval(statusCheckIntervalId);
      statusCheckIntervalId = undefined;
    }
  };

  const checkExistingDocuments = async () => {
    try {
      const response = await api.get("/documents");
      if (response.data && response.data.length > 0) {
        documents.value = response.data;
        novelLoaded.value = true;
        messages.value.push({
          id: Date.now(),
          role: "system",
          content: `Found ${response.data.length} existing document(s): ${response.data
            .map((d: Document) => d.filename)
            .join(", ")}`,
          timestamp: new Date(),
        });
      }
    } catch (error) {
      console.error("Error checking documents:", error);
    }
  };

  // Check for existing documents on initialization
  onMounted(() => {
    checkExistingDocuments();
  });

  const uploadNovel = async (file: File, config: { linesPerPage: number }) => {
    try {
      isProcessing.value = true;
      const formData = new FormData();
      formData.append("file", file);
      formData.append("lines_per_page", config.linesPerPage.toString());

      const response = await api.post("/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      if (response.data.success) {
        currentDocumentId.value = response.data.document_id;
        messages.value.push({
          id: Date.now(),
          role: "system",
          content: "Document upload started. Processing will continue in the background.",
          timestamp: new Date(),
        });

        // Start monitoring processing status
        startStatusCheck();
      }
    } catch (error) {
      messages.value.push({
        id: Date.now(),
        role: "system",
        content: `Upload failed: ${error instanceof Error ? error.message : "Unknown error"}`,
        timestamp: new Date(),
      });
      isProcessing.value = false;
      novelLoaded.value = false;
    }
  };

  const sendMessage = async (message: string) => {
    if (!novelLoaded.value) {
      messages.value.push({
        id: Date.now(),
        role: "system",
        content: "Please upload a novel first.",
        timestamp: new Date(),
      });
      return;
    }

    // Add user message
    messages.value.push({
      id: Date.now(),
      role: "user",
      content: message,
      timestamp: new Date(),
    });

    isLoading.value = true;
    const responseMessageId = Date.now() + 1;
    messages.value.push({
      id: responseMessageId,
      role: "assistant",
      content: "",
      timestamp: new Date(),
    });

    try {
      const response = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: message }),
      });

      if (!response.body) throw new Error("No response body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let done = false;
      let lastMessage = messages.value.find(m => m.id === responseMessageId);

      while (!done) {
        const { value, done: streamDone } = await reader.read();
        done = streamDone;
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          let lines = buffer.split("\n");
          buffer = lines.pop() || ""; // keep incomplete line in buffer
          for (const line of lines) {
            if (!line.trim()) continue;
            try {
              const data = JSON.parse(line);
              if (lastMessage) {
                lastMessage.content = data.answer;
                // Only set references when done is true
                if (data.done && data.references) {
                  lastMessage.references = data.references;
                  isLoading.value = false; // Hide loader when done
                }
              }
            } catch (e) {
              // Ignore parse errors for partial lines
            }
          }
        }
      }
      // Handle any remaining buffer
      if (buffer.trim()) {
        try {
          const data = JSON.parse(buffer);
          if (lastMessage) {
            lastMessage.content = data.answer;
            if (data.done && data.references) {
              lastMessage.references = data.references;
              isLoading.value = false;
            }
          }
        } catch (e) {}
      } else {
        // If no final chunk, hide loader
        isLoading.value = false;
      }
    } catch (error) {
      messages.value.push({
        id: Date.now(),
        role: "system",
        content: `Query failed: ${error instanceof Error ? error.message : "Unknown error"}`,
        timestamp: new Date(),
      });
      isLoading.value = false;
    }
  };

  const clearChat = () => {
    messages.value = [];
  };

  return {
    messages,
    isLoading,
    novelLoaded,
    isProcessing,
    currentDocumentId,
    uploadNovel,
    sendMessage,
    clearChat,
    checkProcessingStatus,
    uploadProgress,
  };
}
