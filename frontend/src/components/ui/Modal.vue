<template>
  <div class="modal-mask" @click.self="$emit('close')">
    <div class="modal-card">
      <header class="modal-header">
        <slot name="title">提示</slot>
      </header>
      <div class="modal-body">
        <slot />
      </div>
      <footer class="modal-footer">
        <slot name="actions" />
      </footer>
    </div>
  </div>
</template>

<script setup>
defineEmits(['close'])
</script>

<style scoped>
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-card {
  background: #111;
  border-radius: 12px;
  padding: 16px;
  min-width: 280px;
}

.modal-header {
  font-weight: 600;
  margin-bottom: 12px;
}

.modal-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
