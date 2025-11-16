from django.db import models
from django.core.validators import MinLengthValidator

class Note(models.Model):
    title = models.CharField(
        max_length=255, 
        validators=[MinLengthValidator(1, "Title cannot be empty")]
    )
    content = models.TextField(
        validators=[MinLengthValidator(1, "Content cannot be empty")]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return self.title
    
    @property
    def character_count(self):
        return len(self.content)
    
    @property 
    def has_blockchain_receipt(self):
        return hasattr(self, 'blockchain_receipt')


class BlockchainReceipt(models.Model):
    note = models.OneToOneField(Note, on_delete=models.CASCADE, related_name='blockchain_receipt')
    transaction_hash = models.CharField(max_length=255)
    block_number = models.IntegerField(blank=True, null=True)
    hash_value = models.CharField(max_length=64, blank=True, null=True)  # SHA-256 hash of note data
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Receipt for {self.note.title} (TX: {self.transaction_hash[:10]}...)"
    
    class Meta:
        verbose_name = "Blockchain Receipt"
        verbose_name_plural = "Blockchain Receipts"
