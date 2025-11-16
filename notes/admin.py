from django.contrib import admin
from .models import Note, BlockchainReceipt

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at',)

@admin.register(BlockchainReceipt)
class BlockchainReceiptAdmin(admin.ModelAdmin):
    list_display = ('note_title', 'transaction_hash_short', 'block_number', 'hash_value_short', 'timestamp')
    search_fields = ('transaction_hash', 'hash_value', 'note__title')
    list_filter = ('timestamp',)
    readonly_fields = ('note', 'transaction_hash', 'block_number', 'hash_value', 'timestamp')
    
    def note_title(self, obj):
        return obj.note.title
    note_title.short_description = 'Note Title'
    
    def transaction_hash_short(self, obj):
        return f"{obj.transaction_hash[:10]}...{obj.transaction_hash[-10:]}"
    transaction_hash_short.short_description = 'Transaction Hash'
    
    def hash_value_short(self, obj):
        if obj.hash_value:
            return f"{obj.hash_value[:10]}...{obj.hash_value[-10:]}"
        return '-'
    hash_value_short.short_description = 'Hash Value'
