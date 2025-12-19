<template>
  <button class="ui-button" :type="type" :disabled="disabled">
    <slot />
  </button>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'button',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
.ui-button {
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
}

.ui-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
