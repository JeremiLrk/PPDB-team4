import commonStyles from "@/style/common/Common.module.css";
import ItemCard from "@/components/common/ItemCard.jsx";

/**
 * MemberCard - a single player line on the public TeamDetail page.
 *
 * Props:
 *   member - { firstName?, lastName? }
 *
 * Intentionally shows no personal information (no email, no ID).
 */
export default function MemberCard({ member }) {
    const fullName = [member.firstName, member.lastName].filter(Boolean).join(" ") || "-";

    return (
        <ItemCard>
            <p className={commonStyles.primaryText}>{fullName}</p>
        </ItemCard>
    );
}
