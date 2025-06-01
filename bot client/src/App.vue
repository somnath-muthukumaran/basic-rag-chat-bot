<template>
  <div class="min-h-screen bg-gray-50 py-8 px-4">
    <div class="max-w-4xl mx-auto">
      <header class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Novel Chat Assistant</h1>
        <p class="text-gray-600">Upload a novel and ask questions about it</p>
      </header>

      <div class="grid grid-cols-1 gap-6">
        <NovelUpload
          @novel-uploaded="handleNovelUpload"
          :is-processing="isProcessing"
        />

        <ChatInterface
          :messages="messages"
          :is-loading="isLoading"
          :novel-loaded="novelLoaded"
          @send-message="handleSendMessage"
          @clear-chat="handleClearChat"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import NovelUpload from "./components/NovelUpload.vue";
import ChatInterface from "./components/ChatInterface.vue";
import { useNovelChatbot } from "./composables/useNovelChatbot";

const {
  messages,
  isLoading,
  novelLoaded,
  isProcessing,
  uploadNovel,
  sendMessage,
  clearChat,
} = useNovelChatbot();

const handleNovelUpload = async (
  file: File,
  config: { linesPerPage: number }
) => {
  await uploadNovel(file, config);
};

const handleSendMessage = async (message: string) => {
  await sendMessage(message);
};

const handleClearChat = () => {
  clearChat();
};
</script>
