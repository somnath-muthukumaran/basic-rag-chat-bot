<template>
  <div
    class="message"
    :class="{
      'flex justify-end': message.role === 'user',
      'flex justify-start': message.role !== 'user',
    }"
  >
    <div
      :class="{
        'bg-primary-600 text-white': message.role === 'user',
        'bg-white text-gray-900': message.role === 'assistant',
        'bg-gray-100 text-gray-700': message.role === 'system',
        'rounded-lg px-4 py-2 max-w-[80%] shadow-sm': true,
      }"
    >
      <p class="whitespace-pre-wrap">{{ message.content }}</p>

      <!-- References section -->
      <div
        v-if="message.references?.length"
        class="mt-3 pt-3 border-t border-gray-200"
      >
        <p class="text-sm font-medium mb-2">References:</p>
        <div
          v-for="ref in message.references"
          :key="ref.page"
          class="text-sm mb-2 p-2 bg-gray-50 rounded"
        >
          <p class="font-medium">
            Page {{ ref.page }}, Lines {{ ref.startLine }}-{{ ref.endLine }}
          </p>
          <p class="mt-1 text-gray-600 text-xs line-clamp-3">
            {{ ref.content }}
          </p>
        </div>
      </div>

      <div class="text-xs opacity-70 mt-2">
        {{ formatTime(message.timestamp) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
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

const props = defineProps<{
  message: Message;
}>();

const formatTime = (date: Date) => {
  return new Date(date).toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
};
</script>
