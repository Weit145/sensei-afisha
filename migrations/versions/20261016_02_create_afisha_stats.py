import sqlalchemy as sa
from alembic import op

revision = "20261016_02"
down_revision = "20261016_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("LOCK TABLE afisha, user_afisha_follows IN SHARE ROW EXCLUSIVE MODE")
    op.create_table(
        "afisha_stats",
        sa.Column(
            "afisha_id",
            sa.Uuid(),
            sa.ForeignKey("afisha.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "followers_count",
            sa.BigInteger(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.CheckConstraint("followers_count >= 0", name="check_afisha_followers_count"),
    )
    op.execute("""
        INSERT INTO afisha_stats (afisha_id, followers_count)
        SELECT a.id, count(f.user_id)
        FROM afisha a
        LEFT JOIN user_afisha_follows f ON f.afisha_id = a.id
        GROUP BY a.id
    """)
    op.execute("""
        CREATE FUNCTION init_afisha_stats() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            INSERT INTO afisha_stats (afisha_id) VALUES (NEW.id);
            RETURN NULL;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_init_afisha_stats
        AFTER INSERT ON afisha
        FOR EACH ROW EXECUTE FUNCTION init_afisha_stats()
    """)
    op.execute("""
        CREATE FUNCTION update_afisha_followers_count() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP = 'TRUNCATE' THEN
                UPDATE afisha_stats SET followers_count = 0;
                RETURN NULL;
            END IF;
            IF TG_OP = 'UPDATE' AND OLD.afisha_id = NEW.afisha_id THEN
                RETURN NULL;
            END IF;
            IF TG_OP IN ('DELETE', 'UPDATE') THEN
                UPDATE afisha_stats
                SET followers_count = followers_count - 1
                WHERE afisha_id = OLD.afisha_id;
            END IF;
            IF TG_OP IN ('INSERT', 'UPDATE') THEN
                UPDATE afisha_stats
                SET followers_count = followers_count + 1
                WHERE afisha_id = NEW.afisha_id;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'Statistics missing for afisha %', NEW.afisha_id;
                END IF;
            END IF;
            RETURN NULL;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER trg_update_afisha_followers_count
        AFTER INSERT OR DELETE OR UPDATE ON user_afisha_follows
        FOR EACH ROW EXECUTE FUNCTION update_afisha_followers_count()
    """)
    op.execute("""
        CREATE TRIGGER trg_reset_afisha_followers_count
        AFTER TRUNCATE ON user_afisha_follows
        FOR EACH STATEMENT EXECUTE FUNCTION update_afisha_followers_count()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER trg_reset_afisha_followers_count ON user_afisha_follows")
    op.execute("DROP TRIGGER trg_update_afisha_followers_count ON user_afisha_follows")
    op.execute("DROP FUNCTION update_afisha_followers_count()")
    op.execute("DROP TRIGGER trg_init_afisha_stats ON afisha")
    op.execute("DROP FUNCTION init_afisha_stats()")
    op.drop_table("afisha_stats")
