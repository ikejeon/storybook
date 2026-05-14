# Payments Readiness Report

This is a scaffold-readiness report. Real App Store / Google Play products, receipt/token verification, and store sandbox purchase tests are still production blockers.

- Premium catalog items needing individual product IDs: 19
- Expected individual product ID pattern: `com.moonjarstories.book.<book-slug-id>`
- Example expected IDs: com.moonjarstories.book.bari_princess_part_1, com.moonjarstories.book.bari_princess_part_2, com.moonjarstories.book.byeoljubu, com.moonjarstories.book.dangun, com.moonjarstories.book.dokkaebi_club
- iOS StoreKit 2 restore scaffold: present
- Android billing abstraction scaffold: present
- Parent gate remains required before purchases/settings by kids-safety validation.
