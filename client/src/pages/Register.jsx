// Page container for Register.

import { Link } from "react-router-dom"
import { useRegister } from "@/hooks/useRegister.js"
import au_styles from "@/style/Authorization.module.css"
import { useCurrentUserContext } from "@/context/useCurrentUserContext"
import { useLangContext } from "@/context/useLangContext.jsx"
import { usePageTexts } from "@/hooks/common/usePageTexts.js"
import { GENDER_SELECT_OPTIONS } from "@/constants/genderOptions.js"

const Register = () => {
    const { lang } = useLangContext()
    const au_texts = usePageTexts("authorization", lang)

    const { setCurrentUser } = useCurrentUserContext()
    const {
        email,
        setEmail,
        password,
        setPassword,
        firstName,
        setFirstName,
        lastName,
        setLastName,
        dateOfBirth,
        setDateOfBirth,
        gender,
        setGender,
        phoneNumber,
        setPhoneNumber,
        handleSubmit,
    } = useRegister(setCurrentUser)
    /*
     Renders the registration form and forwards submission to the auth hook.
    */

    return (
        <div className={au_styles.container}>
            <div className={au_styles.card}>
                <h1 className={au_styles.headerTitle}>{au_texts.register}</h1>

                <form className={au_styles.form} onSubmit={handleSubmit}>
                    <div className={au_styles.nameFieldsRow}>
                        <div className={au_styles.formGroup}>
                            <label
                                htmlFor="register-firstname"
                                className={au_styles.formLabel}
                            >
                                {au_texts.first_name}
                            </label>
                            <input
                                id="register-firstname"
                                type="text"
                                required
                                placeholder={au_texts.placeholder_first_name}
                                value={firstName}
                                onChange={(e) => setFirstName(e.target.value)}
                                className={au_styles.formInput}
                            />
                        </div>

                        <div className={au_styles.formGroup}>
                            <label
                                htmlFor="register-lastname"
                                className={au_styles.formLabel}
                            >
                                {au_texts.last_name}
                            </label>
                            <input
                                id="register-lastname"
                                type="text"
                                required
                                placeholder={au_texts.placeholder_last_name}
                                value={lastName}
                                onChange={(e) => setLastName(e.target.value)}
                                className={au_styles.formInput}
                            />
                        </div>
                    </div>

                    <div className={au_styles.formGroup}>
                        <label
                            htmlFor="register-dateofbirth"
                            className={au_styles.formLabel}
                        >
                            {au_texts.date_of_birth}
                        </label>
                        <input
                            id="register-dateofbirth"
                            type="date"
                            required
                            value={dateOfBirth}
                            onChange={(e) => setDateOfBirth(e.target.value)}
                            className={au_styles.formInput}
                        />
                    </div>

                    <div className={au_styles.nameFieldsRow}>
                        <div className={au_styles.formGroup}>
                            <label
                                htmlFor="register-gender"
                                className={au_styles.formLabel}
                            >
                                Gender
                            </label>
                            <select
                                id="register-gender"
                                required
                                value={gender}
                                onChange={(e) => setGender(e.target.value)}
                                className={au_styles.formInput}
                            >
                                <option value="" disabled>
                                    Select gender
                                </option>
                                {GENDER_SELECT_OPTIONS.map((opt) => (
                                    <option key={opt.value} value={opt.value}>
                                        {opt.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className={au_styles.formGroup}>
                            <label
                                htmlFor="register-phone"
                                className={au_styles.formLabel}
                            >
                                Phone number
                            </label>
                            <input
                                id="register-phone"
                                type="tel"
                                required
                                autoComplete="tel"
                                maxLength={64}
                                value={phoneNumber}
                                onChange={(e) => setPhoneNumber(e.target.value)}
                                className={au_styles.formInput}
                            />
                        </div>
                    </div>

                    <div className={au_styles.formGroup}>
                        <label
                            htmlFor="register-email"
                            className={au_styles.formLabel}
                        >
                            {au_texts.email}
                        </label>
                        <input
                            id="register-email"
                            type="email"
                            required
                            placeholder={au_texts.placeholder_email}
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className={au_styles.formInput}
                        />
                    </div>

                    <div className={au_styles.formGroup}>
                        <label
                            htmlFor="register-password"
                            className={au_styles.formLabel}
                        >
                            {au_texts.password}
                        </label>
                        <input
                            id="register-password"
                            type="password"
                            required
                            placeholder={au_texts.placeholder_password}
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className={au_styles.formInput}
                        />
                    </div>

                    <button type="submit" className={au_styles.formButton}>
                        {au_texts.create_account}
                    </button>
                </form>

                <p className={au_styles.footerText}>
                    {au_texts.has_account}{" "}
                    <Link to="/login" className={au_styles.footerLink}>
                        {au_texts.log_in}
                    </Link>
                </p>

                <Link to="/" className={au_styles.footerLinkGuest}>
                    {au_texts.as_guest}
                </Link>
            </div>
        </div>
    )
}

export default Register
