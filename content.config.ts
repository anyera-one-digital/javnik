import { defineCollection, z } from '@nuxt/content'

const createBaseSchema = () => z.object({
  title: z.string().nonempty(),
  description: z.string().nonempty()
})

export const collections = {
  index: defineCollection({
    source: '0.index.yml',
    type: 'page',
    schema: z.object({
      title: z.string().nonempty(),
      description: z.string().nonempty(),
      seo: z.object({
        title: z.string().optional(),
        description: z.string().optional()
      }).optional(),
      faq: createBaseSchema().extend({
        items: z.array(
          z.object({
            label: z.string().nonempty(),
            content: z.string().nonempty()
          })
        )
      }).optional()
    })
  })
}
