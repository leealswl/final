import React from 'react';
import { Button, CircularProgress } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import useSignOut from '../hooks/userSignOut';
import LoginOutlinedIcon from '@mui/icons-material/LoginOutlined';

export default function LogoutButton({ after = '/' }) {
    const navigate = useNavigate();
    const { mutate: signOut, isPending } = useSignOut({
        onSuccess: () => navigate(after, { replace: true }),
    });

    return (
        <Button disabled={isPending} onClick={() => signOut()}>
            {isPending ? <LoginOutlinedIcon /> : <LoginOutlinedIcon />}
        </Button>
    );
}
