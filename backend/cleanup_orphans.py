
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import sys

    db = SessionLocal()
    from database import SQLALCHEMY_DATABASE_URL
    print(f"Using database: {SQLALCHEMY_DATABASE_URL}")
    try:
        print("Checking for orphaned managed guests...")
        
        # 1. Check for guests managed by 'guest' where the manager guest does not exist
        guests_managed_by_guests = db.query(models.GuestMember).filter(
            models.GuestMember.managed_by_id != None,
            models.GuestMember.managed_by_type == 'guest'
        ).all()
        
        orphaned_count = 0
        for guest in guests_managed_by_guests:
            manager = db.query(models.GuestMember).filter(models.GuestMember.id == guest.managed_by_id).first()
                # Check for name collision in the same group
                existing_same_name = db.query(models.GuestMember).filter(
                    models.GuestMember.group_id == guest.group_id,
                    models.GuestMember.name == guest.name,
                    models.GuestMember.id != guest.id
                ).first()
                
                if existing_same_name:
                    print(f"  Warning: A guest named '{guest.name}' already exists in this group.")
                    guest.name = f"{guest.name} (Recovered)"
                    print(f"  Renaming orphaned guest to: '{guest.name}'")

                guest.managed_by_id = None
                guest.managed_by_type = None
                db.add(guest)
                orphaned_count += 1

        # 2. Check for guests managed by 'user' where the user does not exist (less likely but good sanity check)
        guests_managed_by_users = db.query(models.GuestMember).filter(
            models.GuestMember.managed_by_id != None,
            models.GuestMember.managed_by_type == 'user'
        ).all()

        for guest in guests_managed_by_users:
            manager = db.query(models.User).filter(models.User.id == guest.managed_by_id).first()
            if not manager:
                print(f"Found orphaned guest: {guest.name} (ID: {guest.id}) managed by non-existent User ID: {guest.managed_by_id}")
                
                # Check for name collision in the same group
                existing_same_name = db.query(models.GuestMember).filter(
                    models.GuestMember.group_id == guest.group_id,
                    models.GuestMember.name == guest.name,
                    models.GuestMember.id != guest.id
                ).first()
                
                if existing_same_name:
                    print(f"  Warning: A guest named '{guest.name}' already exists in this group.")
                    guest.name = f"{guest.name} (Recovered)"
                    print(f"  Renaming orphaned guest to: '{guest.name}'")

                guest.managed_by_id = None
                guest.managed_by_type = None
                db.add(guest)
                orphaned_count += 1
        
        if orphaned_count > 0:
            print(f"Fixing {orphaned_count} orphaned guests by un-managing them...")
            db.commit()
            print("Cleanup complete.")
        else:
            print("No orphaned guests found.")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_orphaned_guests()
