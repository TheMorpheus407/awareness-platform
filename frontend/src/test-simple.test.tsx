import { describe, it, expect } from 'vitest'

describe('Simple Test', () => {
  it('should pass basic test', () => {
    expect(1 + 1).toBe(2)
  })

  it('should verify environment', () => {
    expect(typeof window).toBe('undefined')
    expect(typeof global).toBe('object')
  })
})