<template>
  <div v-if="showStatus" class="bg-gray-100 p-4 rounded-lg mb-4">
    <div class="flex justify-between items-center mb-2">
      <h3 class="text-lg font-semibold">Processing Status</h3>
      <button 
        @click="refreshStatus"
        class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded"
      >
        Refresh
      </button>
    </div>
    
    <div class="space-y-2">
      <div class="flex justify-between">
        <span>Status:</span>
        <span :class="{
          'text-yellow-600': status.status === 'processing',
          'text-green-600': status.status === 'completed',
          'text-red-600': status.status === 'error'
        }">{{ status.status }}</span>
      </div>
      
      <div v-if="status.current_document" class="flex justify-between">
        <span>Current File:</span>
        <span>{{ status.current_document }}</span>
      </div>
      
      <div v-if="status.status === 'processing'" class="space-y-1">
        <div class="flex justify-between text-sm">
          <span>Progress:</span>
          <span>{{ Math.round(status.progress) }}%</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            class="bg-blue-500 h-2.5 rounded-full" 
            :style="{ width: status.progress + '%' }"
          ></div>
        </div>
        <div class="flex justify-between text-sm text-gray-600">
          <span>{{ status.processed_chunks }} / {{ status.total_chunks }} chunks</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const props = defineProps<{
  showStatus: boolean
}>()

interface ProcessingStatus {
  status: 'idle' | 'processing' | 'completed' | 'error'
  progress: number
  total_chunks: number
  processed_chunks: number
  current_document: string | null
}

const status = ref<ProcessingStatus>({
  status: 'idle',
  progress: 0,
  total_chunks: 0,
  processed_chunks: 0,
  current_document: null
})

let pollingInterval: NodeJS.Timer | null = null

const fetchStatus = async () => {
  try {
    const response = await axios.get('http://localhost:8000/status')
    if (response.status === 200) {
      status.value = response.data
    }
  } catch (error) {
    console.error('Error fetching status:', error)
  }
}

const refreshStatus = () => {
  fetchStatus()
}

onMounted(() => {
  fetchStatus()
  // Poll every 2 seconds while processing
  pollingInterval = setInterval(() => {
    if (status.value.status === 'processing') {
      fetchStatus()
    }
  }, 2000)
})

onUnmounted(() => {
  if (pollingInterval) {
    clearInterval(pollingInterval)
  }
})
</script>
