from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Note
from web3 import Web3
import json
import hashlib
import logging

# Set up logging
logger = logging.getLogger(__name__)

@csrf_exempt
def create_note_view(request):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            content = request.POST.get('content')
            
            # Validate input
            if not title or not content:
                return JsonResponse({'success': False, 'error': 'Title and content are required'})
            
            # Create and save the note first
            note = Note.objects.create(title=title, content=content)
            logger.info(f"Note created with ID: {note.id}")
            
            # Try blockchain integration
            try:
                w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
                
                if not w3.is_connected():
                    logger.warning("Blockchain not connected, saving note without receipt")
                    return JsonResponse({'success': True, 'note_id': note.id, 'message': 'Note saved (blockchain offline)'})
                
                # Get accounts from Ganache
                accounts = w3.eth.accounts
                if not accounts:
                    logger.warning("No blockchain accounts available")
                    return JsonResponse({'success': True, 'note_id': note.id, 'message': 'Note saved (no blockchain accounts)'})
                
                from_account = accounts[0]
                
                # Compute SHA-256 hash of note data
                note_string = f"{note.id}:{note.title}:{note.content}"
                note_hash = hashlib.sha256(note_string.encode('utf-8')).hexdigest()
                
                # Prepare hash as transaction input
                hash_data = note_hash.encode('utf-8')
                
                # Send a transaction with the hash
                txn = {
                    'from': from_account,
                    'to': from_account,
                    'value': 0,
                    'input': '0x' + hash_data.hex(),
                    'gas': 50000,
                    'gasPrice': w3.to_wei('20', 'gwei'),
                    'nonce': w3.eth.get_transaction_count(from_account),
                    'chainId': 1337  # Ganache default chain ID
                }
                
                # Send transaction
                tx_hash = w3.eth.send_transaction(txn)
                
                # Wait for receipt
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    # Save blockchain receipt
                    from .models import BlockchainReceipt
                    BlockchainReceipt.objects.create(
                        note=note,
                        transaction_hash=tx_hash.hex(),
                        block_number=receipt.blockNumber,
                        hash_value=note_hash
                    )
                    logger.info(f"Blockchain receipt created for note {note.id}")
                    return JsonResponse({'success': True, 'note_id': note.id, 'tx_hash': tx_hash.hex()})
                else:
                    logger.error(f"Blockchain transaction failed for note {note.id}")
                    return JsonResponse({'success': True, 'note_id': note.id, 'message': 'Note saved (blockchain transaction failed)'})
                    
            except Exception as blockchain_error:
                logger.error(f"Blockchain error: {str(blockchain_error)}")
                # Note is already saved, just return success without blockchain
                return JsonResponse({'success': True, 'note_id': note.id, 'message': 'Note saved (blockchain error)'})
                
        except Exception as e:
            logger.error(f"Error creating note: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'notes/create_note.html')

def list_notes(request):
    notes = Note.objects.all().order_by('-created_at')
    return render(request, 'notes/list_notes.html', {'notes': notes})

def edit_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        note.title = request.POST['title']
        note.content = request.POST['content']
        note.save()
        return redirect('list_notes')
    return render(request, 'notes/edit_note.html', {'note': note})

def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        note.delete()
        return redirect('list_notes')
    return render(request, 'notes/delete_note.html', {'note': note})

def verify_receipt(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    receipt = getattr(note, 'blockchain_receipt', None)
    if receipt:
        w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
        try:
            tx_hash = receipt.transaction_hash
            tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
            tx = w3.eth.get_transaction(tx_hash)
            note_string = f"{note.id}:{note.title}:{note.content}"
            computed_hash = hashlib.sha256(note_string.encode('utf-8')).hexdigest()
            hash_match = receipt.hash_value == computed_hash
            input_hex = tx['input'].hex()[2:] if tx['input'] else 'No input data'
            return JsonResponse({
                'tx_hash': tx_hash,
                'status': tx_receipt.status if hasattr(tx_receipt, 'status') else 'Unknown',
                'gas_used': tx_receipt.gasUsed if hasattr(tx_receipt, 'gasUsed') else 'Unknown',
                'input_data': input_hex,
                'hash_match': hash_match,
                'stored_hash': receipt.hash_value,
                'computed_hash': computed_hash
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'No receipt found for this note'}, status=404)
