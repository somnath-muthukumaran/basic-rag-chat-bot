<template>
  <div class="bg-white rounded-lg shadow">
    <div class="border-b p-4">
      <h2 class="text-lg font-semibold">Chat</h2>
    </div>

    <div
      ref="messagesContainer"
      class="h-[500px] overflow-y-auto p-4 space-y-4"
    >
      <div v-if="!novelLoaded" class="text-center text-gray-500 py-8">
        <p>Upload a novel to start chatting!</p>
      </div>

      <ChatMessage
        v-for="message in messages"
        :key="message.timestamp.getTime()"
        :message="message"
      />

      <div v-if="isLoading" class="flex justify-start">
        <div class="bg-gray-100 rounded-lg p-3">
          <span class="text-sm text-gray-600">Thinking...</span>
        </div>
      </div>
    </div>

    <div class="border-t p-4">
      <form @submit.prevent="sendMessage" class="flex gap-2">
        <input
          v-model="inputMessage"
          :disabled="!novelLoaded || isLoading"
          placeholder="Ask about the novel..."
          class="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
        />
        <button
          type="submit"
          :disabled="!inputMessage.trim() || !novelLoaded || isLoading"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import ChatMessage from "./ChatMessage.vue";

const props = defineProps<{
  messages: Array<{
    role: "user" | "assistant";
    content: string;
    references?: Array<{
      page: number;
      startLine: number;
      endLine: number;
      content: string;
    }>;
    timestamp: Date;
  }>;
  isLoading: boolean;
  novelLoaded: boolean;
}>();

const emit = defineEmits<{
  (e: "send-message", message: string): void;
}>();

const inputMessage = ref("");
const messagesContainer = ref<HTMLElement | null>(null);

const sendMessage = () => {
  const message = inputMessage.value.trim();
  if (message) {
    emit("send-message", message);
    inputMessage.value = "";
  }
};

// Auto-scroll to bottom when new messages arrive
watch(
  () => props.messages.length,
  async () => {
    await nextTick();
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  }
);
</script>
