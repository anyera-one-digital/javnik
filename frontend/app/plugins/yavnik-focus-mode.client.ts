export default defineNuxtPlugin(() => {
  if (!import.meta.client) return;

  const root = document.documentElement;
  const markPointer = () => root.classList.add('using-pointer');
  const markKeyboard = (event: KeyboardEvent) => {
    if (event.key === 'Tab' || event.key.startsWith('Arrow') || event.key === 'Enter' || event.key === ' ') {
      root.classList.remove('using-pointer');
    }
  };

  window.addEventListener('pointerdown', markPointer, { passive: true });
  window.addEventListener('keydown', markKeyboard);
});
