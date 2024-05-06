import styles from "../../styles/chat.module.scss";
import Button from "@cloudscape-design/components/button";

export default function Common() {

    return (
        <div>
            <div className={styles.thumbsContainer}>
                <Button
                    variant="icon"
                    iconName={"thumbs-up"}
                    onClick={() => {

                    }}
                />
                <Button
                    iconName={"thumbs-down-filled"}
                    variant="icon"
                    onClick={() => {
                    }}
                />
            </div>
        </div>
    );
}