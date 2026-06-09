export default defineAppConfig({
  ui: {
    colors: {
      primary: 'lime',
      neutral: 'zinc'
    },
    pageHero: {
      slots: {
        container: 'flex flex-col lg:grid py-8 sm:py-12 lg:py-16 gap-16 sm:gap-y-24'
      }
    },
    button: {
      rounded: 'rounded-[30px]',
      default: {
        rounded: 'rounded-[30px]'
      },
      slots: {
        /** Та же высота, что у полей ввода — 44px (touch target) */
        base: 'min-h-[44px] h-[44px] box-border rounded-[30px] font-medium inline-flex items-center justify-center disabled:cursor-not-allowed aria-disabled:cursor-not-allowed disabled:opacity-75 aria-disabled:opacity-75 transition-colors'
      }
    },
    /** Единая высота однострочных полей — 44px (touch target) */
    input: {
      slots: {
        base: 'min-h-[44px] h-[44px] box-border'
      }
    },
    /** Выпадающий список: триггер отдельно от input, задаём ту же высоту 44px */
    select: {
      slots: {
        base: 'min-h-[44px] h-[44px] box-border'
      }
    },
    /** Многострочные поля: минимум 44px по высоте, без фиксированной высоты в одну строку */
    textarea: {
      slots: {
        base: '!h-auto min-h-[44px] box-border'
      }
    },
    /** Отступ между подписью поля и контролом (6px) на всех формах с UFormField */
    formField: {
      variants: {
        orientation: {
          vertical: {
            container: 'mt-[6px]'
          }
        }
      }
    }
  }
})
