import "./style.scss";
import Alert from "@cloudscape-design/components/alert";

export default function ErrorPage() {

  return (
    <div className='container'>
      <Alert
        statusIconAriaLabel="Error"
        type="error"
        header="Not authorized">
      </Alert>
    </div>
  );
}
