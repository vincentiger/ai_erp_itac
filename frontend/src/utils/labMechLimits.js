import { clampText } from '@/utils/dbField'

export const LAB_MECH_HEADER_LIMITS = Object.freeze({
  report_no: 50,
  entrust_no: 50,
  product_name: 100,
  spec_desc: 200,
  lot_no: 50,
  plating: 100,
  material: 100,
  manufacturer: 100,
  standard_type: 30,
  standard_desc: 200,
  tester: 50,
  reviewer: 50,
  remarks: 500,
})

export function clampLabMechHeader(header = {}) {
  const next = { ...header }
  for (const [key, maxLength] of Object.entries(LAB_MECH_HEADER_LIMITS)) {
    if (Object.prototype.hasOwnProperty.call(next, key)) {
      next[key] = clampText(next[key], maxLength)
    }
  }
  return next
}
