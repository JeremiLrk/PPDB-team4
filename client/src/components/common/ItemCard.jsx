// Shared UI building block for ItemCard.

import styles from "@/style/common/Panel.module.css";

export default function ItemCard({ children, className, style }) {
    /*
     Renders one shared list-row container.
    */
    const cls = [styles.listItem, className].filter(Boolean).join(" ");

    return (
        <li className={cls} style={style}>
            {children}
        </li>
    );
}
