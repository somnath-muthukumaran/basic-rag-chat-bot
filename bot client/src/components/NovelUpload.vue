<template>
  <div class="bg-white rounded-lg shadow p-6">
    <h2 class="text-lg font-semibold mb-4">Upload Novel</h2>

    <ProcessingStatus :show-status="showStatus" />

    <div class="space-y-4">
      <div
        class="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center"
        @drop.prevent="handleDrop"
        @dragover.prevent
        @dragenter.prevent="isDragOver = true"
        @dragleave.prevent="isDragOver = false"
        :class="{ 'border-blue-500 bg-blue-50': isDragOver }"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".txt,.pdf"
          @change="handleFileSelect"
          class="hidden"
        />
        <div class="text-gray-600">
          <p class="mb-2">Drop your TXT or PDF file here or</p>
          <button
            @click="$refs.fileInput.click()"
            class="text-blue-600 underline"
          >
            browse files
          </button>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">
          Lines per page
        </label>
        <input
          v-model.number="config.linesPerPage"
          type="number"
          min="10"
          max="50"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg"
        />
        <p class="mt-1 text-sm text-gray-500">
          This affects how the novel is split for references
        </p>
      </div>

      <button
        @click="uploadFile"
        :disabled="!selectedFile || isProcessing"
        class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50"
      >
        {{ isProcessing ? "Processing..." : "Upload & Process" }}
      </button>

      <div v-if="selectedFile" class="text-sm text-gray-600">
        <p><strong>File:</strong> {{ selectedFile.name }}</p>
        <p><strong>Size:</strong> {{ formatFileSize(selectedFile.size) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from "vue";
import ProcessingStatus from './ProcessingStatus.vue';

const emit = defineEmits<{
  (e: "novel-uploaded", file: File, config: { linesPerPage: number }): void;
}>();

const props = defineProps<{
  isProcessing: boolean;
}>();

const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const isDragOver = ref(false);
const showStatus = ref(false);
const config = reactive({
  linesPerPage: 30,
});

// Watch for processing state changes
watch(() => props.isProcessing, (newValue) => {
  if (!newValue) {
    // Hide status after a delay when processing is complete
    setTimeout(() => {
      showStatus.value = false;
    }, 3000);
  }
});

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement;
  if (input.files?.length) {
    const file = input.files[0];
    if (file.type === "text/plain" || file.type === "application/pdf") {
      selectedFile.value = file;
    } else {
      alert("Please upload a TXT or PDF file");
    }
  }
};

const handleDrop = (event: DragEvent) => {
  isDragOver.value = false;
  const files = event.dataTransfer?.files;
  if (files?.length) {
    const file = files[0];
    if (file.type === "text/plain" || file.type === "application/pdf") {
      selectedFile.value = file;
    } else {
      alert("Please upload a TXT or PDF file");
    }
  }
};

const uploadFile = async () => {
  if (selectedFile.value) {
    showStatus.value = true;
    emit("novel-uploaded", selectedFile.value, config);
  }
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};
</script>
