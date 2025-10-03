# Developer Guidelines - LittleLemon API

## Coding Conventions

### Test Creation Guidelines
- **Use helper methods** from `BaseAPITestCase` to reduce code duplication
- **Don't create redundant tests** - avoid testing what's already covered elsewhere
- **Focus on lean, efficient test suite** - test important functionality without unnecessary duplication
- **Ask for permission** before running tests in development

### ViewSet Patterns
- Inherit from appropriate ViewSet (ModelViewSet, ReadOnlyModelViewSet)
- Use `UserGroupManagementMixin` for group management operations
- Implement proper permission classes (`IsStaffOrReadOnly`, `IsAuthenticated`, `IsAdminUser`)
- Add comprehensive logging for create/delete operations

### Model Design Patterns
- Use `full_clean()` in model save() methods for validation
- Implement bleach sanitization in clean() methods for XSS protection
- Use appropriate ForeignKey `on_delete` behaviors (PROTECT for categories)
- Add unique constraints where needed to prevent data duplication

### Serializer Patterns
- Use `UniqueValidator` for fields that should be unique
- Implement custom validation methods for business logic
- Handle overflow protection (e.g., quantity × unit_price validation)
- Provide clear error messages for validation failures

### Common Helper Methods (BaseAPITestCase)
```python
# Authentication
token = self.get_auth_token('username', 'password')
self.authenticate_client(token)

# User Group Management
self.add_user_to_manager_group(user)
self.add_user_to_delivery_crew_group(user)
self.give_user_staff_status(user)

# Debugging
self.print_json(response)  # Set DEBUG_JSON = True in test class
```

### API Response Patterns
- Include comprehensive error messages
- Log important operations (create, delete, group changes)
- Return appropriate HTTP status codes
- Format dates/times consistently in responses

### Database Operation Patterns
- Consider using `transaction.atomic()` for multi-step operations
- Validate non-empty data before processing (e.g., cart before order creation)
- Use select_related/prefetch_related for efficient queries
- Test for proper constraint enforcement